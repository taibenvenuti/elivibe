"""Build and verify the two eliVibe archives from a Git commit."""

import argparse
import gzip
import hashlib
import io
import json
import re
import stat
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STABLE = r"(?:0|[1-9][0-9]*)(?:\.(?:0|[1-9][0-9]*)){2}"
VERSION = re.compile(rf"{STABLE}(?:-rc\.[1-9][0-9]*)?")
COMMIT = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?")
SKILL = "skills/elivibe/SKILL.md"
CODEX_SKILL = "skills/elivibe/agents/openai.yaml"
CODEX_PLUGIN = "skills/.codex-plugin/plugin.json"
CODEX_LICENSE = "skills/LICENSE"
CODEX_CATALOG = ".agents/plugins/marketplace.json"
CODEX_SOURCES = (CODEX_SKILL, CODEX_PLUGIN, CODEX_LICENSE, CODEX_CATALOG)
CODEX_POLICY = b"policy:\n  allow_implicit_invocation: false\n"
LICENSE_ID = "MIT"
ENTRY = "adapters/omp/index.ts"
RUNTIME = (ENTRY, "core/index.ts", SKILL)
NATIVE_SOURCES = (*RUNTIME, "package.json", "LICENSE")
PORTABLE_SOURCES = {
    SKILL: "elivibe/SKILL.md",
    CODEX_SKILL: "elivibe/agents/openai.yaml",
    "LICENSE": "LICENSE",
    "NOTICE": "NOTICE",
}
# Keep the Git/linked root from registering extra resources or duplicate skills.
OTHER_DISCOVERY_PATHS = (
    "tools",
    "hooks",
    "commands",
    "rules",
    "prompts",
    ".mcp.json",
    "mcp.json",
    "plugin.json",
    "marketplace.json",
    ".omp-plugin",
    ".codex-plugin",
    ".claude-plugin",
    "skill",
    ".agents/skills",
    ".claude/skills",
    ".omp/skills",
)
NATIVE = "elivibe-omp"
SUMS = "SHA256SUMS"


def validate_skill(data: bytes) -> None:
    lines = data.decode("utf-8").splitlines()
    if not (
        len(lines) >= 5
        and lines[:2] == ["---", "name: elivibe"]
        and lines[2].startswith("description: ")
        and lines[2].removeprefix("description: ").strip()
        and lines[3:5] == ["disable-model-invocation: true", "---"]
    ):
        raise ValueError("invalid native skill metadata")
    if not any(line.strip() for line in lines[5:]):
        raise ValueError("empty skill body")


def validate_codex_skill(data: bytes) -> None:
    if data != CODEX_POLICY:
        raise ValueError("Codex skill must disable implicit invocation")


def skill_digest(root: Path) -> str:
    for directory, children in (
        ("skills", {"elivibe", ".codex-plugin", "LICENSE"}),
        ("skills/.codex-plugin", {"plugin.json"}),
        ("skills/elivibe", {"SKILL.md", "agents"}),
        ("skills/elivibe/agents", {"openai.yaml"}),
    ):
        path = root / directory
        if not stat.S_ISDIR(path.lstat().st_mode):
            raise ValueError("invalid skill directory")
        if {child.name for child in path.iterdir()} != children:
            raise ValueError("unexpected skill tree")
    for name in (SKILL, CODEX_SKILL):
        mode = (root / name).lstat().st_mode
        if not stat.S_ISREG(mode) or mode & 0o111:
            raise ValueError("invalid skill file mode")
    data = (root / SKILL).read_bytes()
    validate_skill(data)
    validate_codex_skill((root / CODEX_SKILL).read_bytes())
    return hashlib.sha256(data).hexdigest()


def validate_codex(sources: dict[str, bytes], version: str) -> None:
    validate_codex_skill(sources[CODEX_SKILL])
    if sources[CODEX_LICENSE] != sources["LICENSE"]:
        raise ValueError("Codex license differs from the root license")
    plugin = json.loads(sources[CODEX_PLUGIN])
    if not (
        isinstance(plugin, dict)
        and plugin.keys() == {"name", "version", "description", "author", "license", "skills"}
        and plugin["name"] == "elivibe"
        and plugin["version"] == version
        and isinstance(plugin["description"], str)
        and plugin["description"].strip()
        and plugin["author"] == {"name": "Tai Benvenuti"}
        and plugin["license"] == LICENSE_ID
        and plugin["skills"] == "./elivibe"
    ):
        raise ValueError("invalid Codex plugin manifest")
    if json.loads(sources[CODEX_CATALOG]) != {
        "name": "elivibe",
        "interface": {"displayName": "eliVibe"},
        "plugins": [
            {
                "name": "elivibe",
                "source": {"source": "local", "path": "./skills"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Productivity",
            }
        ],
    }:
        raise ValueError("invalid Codex marketplace catalog")


def validate_checkout_metadata(root: Path, version: str) -> None:
    skill_digest(root)
    for directory in (".agents", ".agents/plugins"):
        if not stat.S_ISDIR((root / directory).lstat().st_mode):
            raise ValueError(f"invalid Codex manifest directory: {directory}")
    if {child.name for child in (root / ".agents/plugins").iterdir()} != {"marketplace.json"}:
        raise ValueError("unexpected Codex marketplace tree")
    sources = {}
    for name in (*CODEX_SOURCES, "LICENSE"):
        path = root / name
        mode = path.lstat().st_mode
        if not stat.S_ISREG(mode) or mode & 0o111:
            raise ValueError(f"not a regular non-executable source file: {name}")
        sources[name] = path.read_bytes()
    validate_codex(sources, version)


def git(root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "--no-replace-objects", "-C", str(root), *args],
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise ValueError(f"could not read Git {args[0]} information")
    return result.stdout


def validate_manifest(manifest: object, version: str) -> None:
    if not isinstance(manifest, dict) or manifest.get("version") != version:
        raise ValueError("requested version does not match the committed package.json")
    if (
        manifest.get("name") != "elivibe"
        or manifest.get("license") != LICENSE_ID
        or manifest.get("private")
        or manifest.get("files") != [*RUNTIME, "NOTICE"]
        or manifest.get("omp") != {"extensions": [f"./{ENTRY}"]}
        or any(
            key in manifest
            for key in (
                "engines",
                "devEngines",
                "scripts",
                "dependencies",
                "optionalDependencies",
                "main",
                "exports",
                "pi",
                "browser",
                "bin",
                "peerDependencies",
            )
        )
    ):
        raise ValueError("invalid native package.json")


def release_sources(root: Path, version: str, commit: str) -> dict[str, bytes]:
    if not VERSION.fullmatch(version):
        raise ValueError("expected X.Y.Z or X.Y.Z-rc.N with N positive")
    if not COMMIT.fullmatch(commit):
        raise ValueError("expected a full lowercase Git commit hash")
    if git(root, "rev-parse", "--show-prefix").strip():
        raise ValueError("source root must be the Git checkout root")
    resolved = git(root, "rev-parse", "--verify", f"{commit}^{{commit}}").strip()
    if resolved != commit.encode():
        raise ValueError("revision must be the commit, not a tag object")

    refs = (
        git(root, "for-each-ref", "--format=%(refname:lstrip=2)", "refs/tags")
        .decode()
        .splitlines()
    )
    if f"v{version}" in refs:
        tagged = git(
            root, "rev-parse", "--verify", f"refs/tags/v{version}^{{commit}}"
        ).strip()
        if tagged != commit.encode():
            raise ValueError(f"v{version} does not point to the supplied commit")

    entries = {}
    notice_names = ("LICENSE", "NOTICE")
    tree = git(
        root,
        "ls-tree",
        "-r",
        "-z",
        commit,
        "--",
        *NATIVE_SOURCES,
        "skills",
        ".agents/plugins",
        "NOTICE",
        *OTHER_DISCOVERY_PATHS,
    )
    for entry in tree.split(b"\0")[:-1]:
        info, path = entry.split(b"\t", 1)
        mode, kind, oid = info.split()
        entries[path] = (mode, kind, oid)
    for path in OTHER_DISCOVERY_PATHS:
        name = path.encode()
        if any(entry == name or entry.startswith(name + b"/") for entry in entries):
            raise ValueError(f"unexpected OMP discovery path: {path}")
    if {name for name in entries if name.startswith(b"skills/")} != {
        name.encode() for name in (SKILL, CODEX_SKILL, CODEX_PLUGIN, CODEX_LICENSE)
    }:
        raise ValueError("unexpected skill tree")
    if {
        name
        for name in entries
        if name == b".agents/plugins" or name.startswith(b".agents/plugins/")
    } != {CODEX_CATALOG.encode()}:
        raise ValueError("unexpected Codex marketplace tree")
    sources = {}
    required = (*NATIVE_SOURCES, *CODEX_SOURCES)
    if b"NOTICE" in entries:
        required = (*required, "NOTICE")
    for name in required:
        mode, kind, oid = entries.get(name.encode(), (b"", b"", b""))
        if (mode, kind) != (b"100644", b"blob"):
            raise ValueError(f"not a regular non-executable source file: {name}")
        sources[name] = git(root, "cat-file", "blob", oid.decode("ascii"))
        if name in notice_names and not sources[name].strip():
            raise ValueError(f"empty distribution notice: {name}")
    validate_skill(sources[SKILL])
    validate_codex(sources, version)
    validate_manifest(json.loads(sources["package.json"]), version)
    return sources


def artifacts(
    root: Path,
    version: str,
    commit: str,
    license_id: str | None = None,
) -> dict[str, bytes]:
    if license_id is not None and (
        license_id != LICENSE_ID or not re.fullmatch(STABLE, version)
    ):
        raise ValueError(f"--license-id must be {LICENSE_ID} and use a stable version")
    sources = release_sources(root, version, commit)
    portable = io.BytesIO()
    with zipfile.ZipFile(portable, "w") as archive:
        for source, name in PORTABLE_SOURCES.items():
            if source in sources:
                member = zipfile.ZipInfo(name)
                member.create_system = 3
                member.external_attr = (stat.S_IFREG | 0o644) << 16
                archive.writestr(member, sources[source])
    native = io.BytesIO()
    with (
        gzip.GzipFile(filename="", fileobj=native, mode="wb", mtime=0) as compressed,
        tarfile.open(
            fileobj=compressed, mode="w", format=tarfile.USTAR_FORMAT
        ) as archive,
    ):
        for name in (*NATIVE_SOURCES, "NOTICE"):
            if name in sources:
                member = tarfile.TarInfo(f"{NATIVE}/{name}")
                member.size = len(sources[name])
                archive.addfile(member, io.BytesIO(sources[name]))
    files = {
        f"elivibe-{version}.zip": portable.getvalue(),
        f"{NATIVE}-{version}.tar.gz": native.getvalue(),
    }
    files[SUMS] = "".join(
        f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in files.items()
    ).encode()
    return files


def build(output: Path, files: dict[str, bytes]) -> None:
    if not stat.S_ISDIR(output.lstat().st_mode):
        raise ValueError("output must be an existing directory, not a symlink")
    if any(output.iterdir()):
        raise ValueError("output directory must be empty")
    written = []
    try:
        for name, data in files.items():
            path = output / name
            with path.open("xb") as stream:
                written.append(path)
                stream.write(data)
    except OSError:
        for path in written:
            path.unlink()
        raise


def verify(output: Path, files: dict[str, bytes]) -> None:
    if not stat.S_ISDIR(output.lstat().st_mode):
        raise ValueError("output must be an existing directory, not a symlink")
    if {path.name for path in output.iterdir()} != files.keys():
        raise ValueError("unexpected or missing release assets")
    # Compare the complete archives, including every header, before any extraction.
    for name, data in files.items():
        path = output / name
        mode = path.lstat()
        if (
            not stat.S_ISREG(mode.st_mode)
            or mode.st_size != len(data)
            or path.read_bytes() != data
        ):
            raise ValueError(f"asset differs from the canonical build: {name}")


def inspect_install(files: dict[str, bytes], version: str) -> None:
    # Only extract in-memory archives from the canonical build, not supplied files.
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        with zipfile.ZipFile(io.BytesIO(files[f"elivibe-{version}.zip"])) as archive:
            archive.extractall(root)
        with tarfile.open(
            fileobj=io.BytesIO(files[f"{NATIVE}-{version}.tar.gz"])
        ) as archive:
            archive.extractall(root, filter="data")
        skill = root / "elivibe/SKILL.md"
        validate_codex_skill((root / PORTABLE_SOURCES[CODEX_SKILL]).read_bytes())
        plugin = root / NATIVE
        discovered = plugin / SKILL
        manifest = json.loads((plugin / "package.json").read_bytes())
        if not stat.S_ISREG(discovered.lstat().st_mode):
            raise ValueError("unexpected native skill discovery path")
        if (
            discovered.read_bytes() != skill.read_bytes()
            or (root / "LICENSE").read_bytes() != (plugin / "LICENSE").read_bytes()
            or manifest["license"] != LICENSE_ID
            or manifest["version"] != version
        ):
            raise ValueError("extracted portable and native package metadata differ")
        print(f"Skill SHA-256: {hashlib.sha256(skill.read_bytes()).hexdigest()}")
        print(f"Native manifest: {json.dumps(manifest)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "verify", "rehearse"))
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument(
        "--output-dir", type=Path, help="existing empty directory for build"
    )
    parser.add_argument("--version", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument(
        "--license-id", help=f"assert {LICENSE_ID} for a stable release"
    )
    args = parser.parse_args()
    if (args.output_dir is None) != (args.command == "rehearse"):
        parser.error(
            "--output-dir is required for build/verify and forbidden for rehearse"
        )
    source = (
        args.source_root,
        args.version,
        args.commit,
        args.license_id,
    )
    try:
        files = artifacts(*source)
        if args.command == "build":
            build(args.output_dir, files)
        elif args.command == "verify":
            verify(args.output_dir, files)
        else:
            with (
                tempfile.TemporaryDirectory() as first,
                tempfile.TemporaryDirectory() as second,
            ):
                build(Path(first), files)
                build(Path(second), artifacts(*source))
                verify(Path(first), files)
                verify(Path(second), files)
            print(f"{args.version} from {args.commit}")
            inspect_install(files, args.version)
            print(files[SUMS].decode(), end="")
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
