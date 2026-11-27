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

from dev import package

ROOT = Path(__file__).resolve().parents[2]
VERSION = json.loads((ROOT / "package.json").read_bytes())["version"]
SOURCES = (
    "adapters/omp/index.ts",
    "core/index.ts",
    "skills/elivibe/SKILL.md",
    "package.json",
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


def test_package_round_trip(source, tmp_path):
    root, sha = source
    (root / SOURCES[0]).write_bytes(b"unreviewed worktree edit")
    (root / "LICENSE").write_bytes(b"unreviewed license edit")
    (root / "package.json").write_bytes(b"unreviewed manifest edit")
    checked = tmp_path / "checked"
    checked.mkdir()
    command = [
        sys.executable,
        str(ROOT / "dev/package.py"),
        "build",
        "--source-root",
        str(root),
        "--output-dir",
        str(checked),
        "--version",
        VERSION,
        "--commit",
        sha,
    ]
    subprocess.run(command, check=True)
    command[2] = "verify"
    subprocess.run(command, check=True)

    other = tmp_path / "other"
    other.mkdir()
    expected = package.artifacts(root, VERSION, sha, license_id="MIT")
    package.build(other, expected)
    assert {path.name: path.read_bytes() for path in checked.iterdir()} == {
        path.name: path.read_bytes() for path in other.iterdir()
    }
    portable = f"elivibe-{VERSION}.zip"
    native = f"elivibe-omp-{VERSION}.tar.gz"
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
        assert archive.getnames() == [f"elivibe-omp/{path}" for path in SOURCES]
        assert all(member.isfile() for member in archive.getmembers())
        archive.extractall(install, filter="data")
    plugin = install / "elivibe-omp"
    for relative in SOURCES:
        assert (plugin / relative).read_bytes() == (ROOT / relative).read_bytes()
    skill = plugin / "skills/elivibe/SKILL.md"
    assert skill.read_bytes() == (install / "elivibe/SKILL.md").read_bytes()


def test_package_version_and_tag_require_exact_commit(source):
    root, first = source
    with pytest.raises(ValueError, match="does not match the committed package.json"):
        package.artifacts(root, "0.1.0", first)
    git(root, "tag", f"v{VERSION}", first)
    (root / "unrelated").write_text("another commit")
    with pytest.raises(ValueError, match="does not point to the supplied commit"):
        package.artifacts(root, VERSION, commit(root))
    assert package.artifacts(root, VERSION, first)


def test_offline_npm_pack_agrees_with_checkout_and_release(source, tmp_path):
    root, _ = source
    (root / "README.md").write_text("# eliVibe\n")
    (root / "NOTICE").write_text("Optional notice\n")
    (root / "excluded.txt").write_text("not a runtime file\n")
    files = package.artifacts(root, VERSION, commit(root))
    subprocess.run(
        [
            "npm",
            "pack",
            "--ignore-scripts",
            "--offline",
            "--cache",
            str(tmp_path / "npm-cache"),
            "--pack-destination",
            str(tmp_path),
        ],
        cwd=root,
        env={
            "PATH": os.environ["PATH"],
            "HOME": str(tmp_path),
            "NPM_CONFIG_USERCONFIG": str(tmp_path / "npm-user"),
            "NPM_CONFIG_GLOBALCONFIG": str(tmp_path / "npm-global"),
        },
        check=True,
    )
    with (
        tarfile.open(tmp_path / f"elivibe-{VERSION}.tgz") as npm,
        tarfile.open(
            fileobj=io.BytesIO(files[f"elivibe-omp-{VERSION}.tar.gz"])
        ) as native,
    ):
        assert set(npm.getnames()) == {
            f"package/{path}" for path in (*SOURCES, "NOTICE", "README.md")
        }
        assert all(member.isfile() for member in npm.getmembers())
        for path in (*SOURCES, "NOTICE"):
            assert (
                npm.extractfile(f"package/{path}").read()
                == native.extractfile(f"elivibe-omp/{path}").read()
                == (root / path).read_bytes()
            )


@pytest.mark.parametrize(
    "overrides",
    [
        {"engines": {"node": ">=24"}},
        {"scripts": {"prepare": "false"}},
        {"private": True},
        {"files": ["tests"]},
        {"main": "excluded.txt"},
        {"omp": {"extensions": []}},
    ],
)
def test_invalid_committed_manifest_rejected(source, overrides):
    root, _ = source
    path = root / "package.json"
    manifest = json.loads(path.read_bytes())
    path.write_text(json.dumps({**manifest, **overrides}))
    with pytest.raises(ValueError, match="invalid native package.json"):
        package.artifacts(root, VERSION, commit(root))


def test_unexpected_committed_omp_discovery_path_rejected(source):
    root, _ = source
    (root / "tools").mkdir()
    (root / "tools/example.ts").write_text("export default {};\n")
    with pytest.raises(ValueError, match="unexpected OMP discovery path: tools"):
        package.artifacts(root, VERSION, commit(root))


def test_missing_committed_license_rejected(source):
    root, _ = source
    license_path = root / "LICENSE"
    license_path.unlink()
    sha = commit(root)
    license_path.write_bytes((ROOT / "LICENSE").read_bytes())
    with pytest.raises(ValueError, match="source file: LICENSE"):
        package.artifacts(root, VERSION, sha)


def test_optional_notice_bundled_outside_skill(source):
    root, _ = source
    (root / "NOTICE").write_bytes(b"synthetic notice")
    files = package.artifacts(root, VERSION, commit(root))
    with zipfile.ZipFile(io.BytesIO(files[f"elivibe-{VERSION}.zip"])) as archive:
        assert archive.namelist() == ["elivibe/SKILL.md", "LICENSE", "NOTICE"]
        assert archive.read("NOTICE") == b"synthetic notice"
    with tarfile.open(
        fileobj=io.BytesIO(files[f"elivibe-omp-{VERSION}.tar.gz"])
    ) as archive:
        assert archive.extractfile("elivibe-omp/NOTICE").read() == b"synthetic notice"


@pytest.mark.parametrize(
    ("version", "license_id"), [(VERSION, "BSD-3-Clause"), (f"{VERSION}-rc.2", "MIT")]
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
        package.artifacts(root, VERSION, "HEAD")


@pytest.mark.parametrize(
    "relative", [SOURCES[0], SOURCES[2], "package.json", "LICENSE"]
)
def test_package_rejects_committed_symlinks(source, relative):
    root, _ = source
    path = root / relative
    path.unlink()
    path.symlink_to("../outside")
    with pytest.raises(ValueError, match="not a regular non-executable source file"):
        package.artifacts(root, VERSION, commit(root))


def test_verify_rejects_altered_archive_even_with_matching_checksums(source, tmp_path):
    root, sha = source
    output = tmp_path / "assets"
    output.mkdir()
    files = package.artifacts(root, VERSION, sha)
    package.build(output, files)
    with pytest.raises(ValueError, match="directory must be empty"):
        package.build(output, files)
    path = output / f"elivibe-{VERSION}.zip"
    with zipfile.ZipFile(path, "a") as archive:
        archive.writestr("../escape", "must not be extracted")
    sums = output / "SHA256SUMS"
    lines = sums.read_text().splitlines()
    lines[0] = f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}"
    sums.write_text("\n".join(lines) + "\n")
    with pytest.raises(ValueError, match="asset differs from the canonical build"):
        package.verify(output, files)
