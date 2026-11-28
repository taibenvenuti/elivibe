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
    "README.md",
)
CODEX_SKILL = "skills/elivibe/agents/openai.yaml"
CODEX_PLUGIN = "skills/.codex-plugin/plugin.json"
CODEX_CATALOG = ".agents/plugins/marketplace.json"
CODEX_LICENSE = "skills/LICENSE"
PLUGIN_ICON = "skills/icon.png"
CLAUDE_CATALOG = ".claude-plugin/marketplace.json"
CLAUDE_PLUGIN = "skills/.claude-plugin/plugin.json"
CLAUDE_README = "skills/README.md"
PORTABLE_CODEX = "elivibe/agents/openai.yaml"
PORTABLE_FILES = ["elivibe/SKILL.md", PORTABLE_CODEX, "LICENSE", "README.md"]
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
    for relative in (
        *SOURCES,
        CODEX_SKILL,
        CODEX_PLUGIN,
        CODEX_CATALOG,
        CODEX_LICENSE,
        PLUGIN_ICON,
        CLAUDE_CATALOG,
        CLAUDE_PLUGIN,
        CLAUDE_README,
    ):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((ROOT / relative).read_bytes())
    return root, commit(root)


def test_package_round_trip(source, tmp_path):
    root, sha = source
    (root / SOURCES[0]).write_bytes(b"unreviewed worktree edit")
    (root / "LICENSE").write_bytes(b"unreviewed license edit")
    (root / "README.md").write_bytes(b"unreviewed readme edit")
    (root / "package.json").write_bytes(b"unreviewed manifest edit")
    (root / CODEX_SKILL).write_bytes(b"unreviewed policy edit")
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
        assert archive.namelist() == PORTABLE_FILES
        assert archive.read(PORTABLE_CODEX) == (ROOT / CODEX_SKILL).read_bytes()
        assert all(not member.is_dir() for member in archive.infolist())
        assert archive.read("LICENSE") == (ROOT / "LICENSE").read_bytes()
        assert archive.read("README.md") == (ROOT / "README.md").read_bytes()
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
            f"package/{path}" for path in (*SOURCES, "NOTICE")
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
        {"pi": {"skills": ["./other"]}},
    ],
)
def test_invalid_committed_manifest_rejected(source, overrides):
    root, _ = source
    path = root / "package.json"
    manifest = json.loads(path.read_bytes())
    path.write_text(json.dumps({**manifest, **overrides}))
    with pytest.raises(ValueError, match="invalid native package.json"):
        package.artifacts(root, VERSION, commit(root))


@pytest.mark.parametrize(
    "relative",
    [
        "tools/example.ts",
        "plugin.json",
        ".codex-plugin/plugin.json",
        "marketplace.json",
        ".agents/skills/extra/SKILL.md",
    ],
)
def test_unexpected_committed_omp_discovery_path_rejected(source, relative):
    root, _ = source
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("unexpected discovery surface\n")
    with pytest.raises(ValueError, match="unexpected OMP discovery path"):
        package.artifacts(root, VERSION, commit(root))


@pytest.mark.parametrize(
    "content",
    [
        b"policy:\n  allow_implicit_invocation: true\n",
        b"policy:\n  allow_implicit_invocation: false\npolicy: {}\n",
    ],
)
def test_committed_codex_policy_cannot_enable_implicit_invocation(source, content):
    root, _ = source
    (root / CODEX_SKILL).write_bytes(content)
    with pytest.raises(
        ValueError, match="Codex skill must disable implicit invocation"
    ):
        package.artifacts(root, VERSION, commit(root))


@pytest.mark.parametrize(
    ("relative", "old", "replacement", "error"),
    [
        (CODEX_PLUGIN, b"./elivibe", b"..", "invalid Codex plugin manifest"),
        (CODEX_PLUGIN, VERSION.encode(), b"9.9.9", "invalid Codex plugin manifest"),
        (
            CODEX_PLUGIN,
            b"./icon.png",
            b"../icon.png",
            "invalid Codex plugin directory metadata",
        ),
        (
            CODEX_PLUGIN,
            b'"capabilities": []',
            b'"capabilities": ["Read"]',
            "invalid Codex plugin directory metadata",
        ),
        (CODEX_CATALOG, b"./skills", b"./", "invalid Codex marketplace catalog"),
        (CODEX_LICENSE, b"MIT License", b"Changed", "Codex license differs"),
        (PLUGIN_ICON, b"\x89PNG", b"<svg", "plugin icon must be a 64x64 PNG"),
        (CLAUDE_PLUGIN, b"./elivibe", b"..", "invalid Claude plugin manifest"),
        (CLAUDE_PLUGIN, VERSION.encode(), b"9.9.9", "invalid Claude plugin manifest"),
        (CLAUDE_CATALOG, b"./skills", b"./", "invalid Claude marketplace catalog"),
    ],
)
def test_committed_host_metadata_rejects_drift(
    source, relative, old, replacement, error
):
    root, _ = source
    path = root / relative
    path.write_bytes(path.read_bytes().replace(old, replacement))
    with pytest.raises(ValueError, match=error):
        package.artifacts(root, VERSION, commit(root))


def test_committed_compatibility_catalog_cannot_add_omp_root_manifest(source):
    root, sha = source
    (root / ".claude-plugin/plugin.json").write_text("{}")
    package.validate_checkout_metadata(root, VERSION)
    assert package.artifacts(root, VERSION, sha)
    with pytest.raises(ValueError, match="unexpected marketplace tree"):
        package.artifacts(root, VERSION, commit(root))


def test_committed_claude_readme_must_meet_directory_minimum(source):
    root, _ = source
    (root / CLAUDE_README).write_text("Too short.")
    with pytest.raises(
        ValueError, match="Claude plugin README must have at least 40 words"
    ):
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
        assert archive.namelist() == [*PORTABLE_FILES, "NOTICE"]
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
    "relative",
    [
        SOURCES[0],
        SOURCES[2],
        "package.json",
        "LICENSE",
        CODEX_SKILL,
        CODEX_PLUGIN,
        PLUGIN_ICON,
        CLAUDE_PLUGIN,
    ],
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
