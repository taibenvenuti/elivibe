import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

from tools import package

ROOT = Path(__file__).resolve().parents[2]
SOURCES = (
    "adapters/omp/index.ts",
    "core/index.ts",
    "providers/jev.ts",
    "skill/elivibe/SKILL.md",
    "LICENSE",
)
GIT_ENV = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}


def git(root, *args):
    return subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            *args,
        ],
        env=GIT_ENV,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def commit(root):
    git(root, "add", ".")
    git(root, "commit", "-qm", "chore: fixture")
    return git(root, "rev-parse", "HEAD")


@pytest.fixture
def source(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    git(root, "init", "-q", "--initial-branch=main", "--template=")
    for relative in SOURCES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((ROOT / relative).read_bytes())
    return root, commit(root)


@pytest.mark.parametrize("version", ["0.1.0", "0.1.0-rc.2"])
def test_package_round_trip(source, tmp_path, version):
    root, sha = source
    (root / SOURCES[0]).write_bytes(b"unreviewed worktree edit")
    (root / "LICENSE").write_bytes(b"unreviewed license edit")
    checked = tmp_path / "checked"
    checked.mkdir()
    command = [
        sys.executable,
        str(ROOT / "tools/package.py"),
        "build",
        "--source-root",
        str(root),
        "--output-dir",
        str(checked),
        "--version",
        version,
        "--commit",
        sha,
    ]
    if version == "0.1.0":
        command.append("--bootstrap")
    subprocess.run(command, check=True)
    command[2] = "verify"
    subprocess.run(command, check=True)

    other = tmp_path / "other"
    other.mkdir()
    expected = package.artifacts(
        root, version, sha, license_id="MIT" if version == "0.1.0" else None
    )
    package.build(other, expected)
    assert {path.name: path.read_bytes() for path in checked.iterdir()} == {
        path.name: path.read_bytes() for path in other.iterdir()
    }
    portable = f"elivibe-{version}.zip"
    native = f"elivibe-omp-{version}.tar.gz"
    assert (checked / "SHA256SUMS").read_text().splitlines() == [
        f"{hashlib.sha256((checked / name).read_bytes()).hexdigest()}  {name}"
        for name in (portable, native)
    ]

    install = tmp_path / "install"
    install.mkdir()
    with zipfile.ZipFile(checked / portable) as archive:
        assert archive.namelist() == ["elivibe/SKILL.md", "LICENSE"]
        assert archive.read("LICENSE") == (ROOT / "LICENSE").read_bytes()
        archive.extractall(install)
    with tarfile.open(checked / native) as archive:
        assert archive.getnames() == [
            *(f"elivibe-omp/{source}" for source in SOURCES),
            "elivibe-omp/package.json",
            "elivibe-omp/skills",
        ]
        link = archive.getmember("elivibe-omp/skills")
        assert link.issym() and link.linkname == "skill"
        archive.extractall(install, filter="data")
    plugin = install / "elivibe-omp"
    for relative in SOURCES:
        assert (plugin / relative).read_bytes() == (ROOT / relative).read_bytes()
    manifest = json.loads((plugin / "package.json").read_bytes())
    assert manifest == {
        "name": "elivibe",
        "version": version,
        "private": True,
        "license": "MIT",
        "omp": {"extensions": ["./adapters/omp/index.ts"]},
    }
    skill = plugin / "skills/elivibe/SKILL.md"
    assert skill.resolve(strict=True) == plugin / "skill/elivibe/SKILL.md"
    assert skill.read_bytes() == (install / "elivibe/SKILL.md").read_bytes()


def test_bootstrap_and_tag_require_exact_version_and_commit(source):
    root, first = source
    assert package.artifacts(root, "0.1.0", first, bootstrap=True)
    with pytest.raises(ValueError, match="bootstrap requires 0.1.0"):
        package.artifacts(root, "1.0.0", first, bootstrap=True)
    git(root, "tag", "v0.1.0", first)
    with pytest.raises(ValueError, match="no existing stable release tag"):
        package.artifacts(root, "0.1.0", first, bootstrap=True)
    (root / "unrelated").write_text("another commit")
    with pytest.raises(ValueError, match="does not point to the supplied commit"):
        package.artifacts(root, "0.1.0", commit(root))
    assert package.artifacts(root, "0.1.0", first)


def test_missing_committed_license_rejected(source):
    root, _ = source
    license_path = root / "LICENSE"
    license_path.unlink()
    sha = commit(root)
    license_path.write_bytes((ROOT / "LICENSE").read_bytes())
    with pytest.raises(ValueError, match="source file: LICENSE"):
        package.artifacts(root, "0.1.1", sha)


def test_optional_notice_bundled_outside_skill(source):
    root, _ = source
    (root / "NOTICE").write_bytes(b"synthetic notice")
    files = package.artifacts(root, "0.1.1", commit(root))
    with zipfile.ZipFile(io.BytesIO(files["elivibe-0.1.1.zip"])) as archive:
        assert archive.namelist() == ["elivibe/SKILL.md", "LICENSE", "NOTICE"]
        assert archive.read("NOTICE") == b"synthetic notice"
    with tarfile.open(fileobj=io.BytesIO(files["elivibe-omp-0.1.1.tar.gz"])) as archive:
        assert archive.extractfile("elivibe-omp/NOTICE").read() == b"synthetic notice"


@pytest.mark.parametrize(
    ("version", "license_id"), [("0.1.0", "BSD-3-Clause"), ("0.1.0-rc.2", "MIT")]
)
def test_package_rejects_invalid_license_assertion(source, version, license_id):
    root, sha = source
    with pytest.raises(ValueError, match="--license-id must be MIT"):
        package.artifacts(root, version, sha, license_id=license_id)


@pytest.mark.parametrize(
    "version", ["../0.1.0", "0.1.0-rc.0", "0.1.0;touch x", "--help"]
)
def test_package_rejects_invalid_versions(source, version):
    root, sha = source
    with pytest.raises(ValueError, match="expected X.Y.Z"):
        package.artifacts(root, version, sha)
    with pytest.raises(ValueError, match="expected a full"):
        package.artifacts(root, "0.1.0", "HEAD")


@pytest.mark.parametrize("relative", [SOURCES[0], "skill/elivibe/SKILL.md", "LICENSE"])
def test_package_rejects_committed_symlinks(source, relative):
    root, _ = source
    path = root / relative
    path.unlink()
    path.symlink_to("../outside")
    with pytest.raises(ValueError, match="not a regular non-executable source file"):
        package.artifacts(root, "0.1.0", commit(root))


def test_verify_rejects_altered_archive_even_with_matching_checksums(source, tmp_path):
    root, sha = source
    output = tmp_path / "assets"
    output.mkdir()
    files = package.artifacts(root, "0.1.0", sha)
    package.build(output, files)
    with pytest.raises(ValueError, match="directory must be empty"):
        package.build(output, files)
    path = output / "elivibe-0.1.0.zip"
    with zipfile.ZipFile(path, "a") as archive:
        archive.writestr("../escape", "must not be extracted")
    sums = output / "SHA256SUMS"
    lines = sums.read_text().splitlines()
    lines[0] = f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}"
    sums.write_text("\n".join(lines) + "\n")
    with pytest.raises(ValueError, match="asset differs from the canonical build"):
        package.verify(output, files)
