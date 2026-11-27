"""Validate checked-in development configuration, active docs and commit subjects."""

import json
import os
import re
import subprocess
import sys
import tomllib
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

from package import validate_checkout_metadata, validate_manifest

SUBJECT = re.compile(r"[a-z]+(?:\([^\s()]+\))?!?: \S[^\r\n]*")
LINK = re.compile(r"\[[^\]]+\]\(([^\s)]+)\)")
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
NODE_VERSION = "24.21.0"
DOCS = (
    "AGENTS.md",
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    "skills/elivibe/SKILL.md",
    "design/adr/0004-conceptual-explanation-and-native-integration.md",
    "design/adr/0005-host-managed-teaching-and-distribution.md",
    "design/adr/0006-one-skill-host-owned-invocation.md",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def configuration() -> None:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    require(
        project["tool"]["pytest"]["ini_options"]["testpaths"] == ["tests/product"],
        "pytest must select only product tests by default",
    )
    manifest = json.loads(Path("package.json").read_bytes())
    validate_manifest(manifest, project["project"]["version"])
    validate_checkout_metadata(Path.cwd(), manifest["version"])
    lock = json.loads(Path("package-lock.json").read_bytes())
    packages = lock["packages"]
    locked_root = packages[""]
    require(
        lock["lockfileVersion"] == 3
        and all(lock[k] == manifest[k] for k in ("name", "version"))
        and all(
            locked_root[k] == manifest[k]
            for k in ("name", "version", "license", "devDependencies")
        )
        and "engines" not in locked_root,
        "npm lock root does not match package.json",
    )
    version = subprocess.check_output(["node", "--version"], text=True).strip()
    require(
        version == "v" + NODE_VERSION,
        f"expected Node {NODE_VERSION}, got {version}",
    )
    for name, pin in manifest["devDependencies"].items():
        require(
            re.fullmatch(r"\d+\.\d+\.\d+", pin) is not None
            and packages[f"node_modules/{name}"]["version"] == pin,
            f"{name} must be locked to its exact development pin",
        )
    for path, entry in packages.items():
        if not path:
            continue
        require(entry.get("dev") is True, f"{path} is not development-only")
        if not entry.get("inBundle"):
            source = urlsplit(entry.get("resolved", ""))
            require(
                source.scheme == "https"
                and source.netloc == "registry.npmjs.org"
                and entry.get("integrity", "").startswith("sha512-"),
                f"{path} lacks an integrity-pinned npm registry source",
            )
    uv_lock = tomllib.loads(Path("uv.lock").read_text(encoding="utf-8"))
    require(
        any(
            entry["source"] == {"virtual": "."}
            and entry["name"] == project["project"]["name"]
            and entry["version"] == manifest["version"]
            for entry in uv_lock["package"]
        ),
        "uv lock root does not match the developer project and package version",
    )
    for entry in uv_lock["package"]:
        require(
            entry["source"]
            in ({"virtual": "."}, {"registry": "https://pypi.org/simple"}),
            f"unexpected uv source for {entry['name']}",
        )
    options = json.loads(Path("tsconfig.json").read_bytes())["compilerOptions"]
    require(
        options.get("strict") is True and options.get("noEmit") is True,
        "TypeScript checking must be strict and no-emit",
    )


def markdown(path: Path, *, shell: bool = False) -> list[tuple[int, str]]:
    outside = []
    marker = language = ""
    body = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        fence = FENCE.fullmatch(line)
        if not marker:
            if fence:
                marker, language = fence.groups()
            else:
                outside.append((number, line))
        elif fence and fence[1].startswith(marker) and not fence[2].strip():
            if shell and language.strip() in {"sh", "bash"}:
                result = subprocess.run(
                    [language.strip(), "-n"],
                    input="\n".join(body),
                    text=True,
                    check=False,
                )
                require(
                    result.returncode == 0, f"{path}:{number}: invalid shell example"
                )
            marker = ""
            body.clear()
        else:
            body.append(line)
    require(not marker, f"{path}: unclosed Markdown fence")
    return outside


def anchors(lines: list[tuple[int, str]]) -> set[str]:
    used: Counter[str] = Counter()
    found = set()
    for _, line in lines:
        if heading := HEADING.fullmatch(line):
            label = re.sub(r"\s+#+$", "", heading[1])
            label = LINK.sub(lambda link: link[0].split("]", 1)[0][1:], label)
            slug = re.sub(r"[^\w -]", "", label.lower()).replace(" ", "-")
            candidate = slug
            while candidate in found:
                used[slug] += 1
                candidate = f"{slug}-{used[slug]}"
            found.add(candidate)
    return found


def documentation(root: Path) -> None:
    files = [root / doc for doc in DOCS]
    files += sorted((root / "docs").glob("*.md"))
    headings = {}
    for path in files:
        for number, line in markdown(path, shell=True):
            for match in LINK.finditer(line):
                link = urlsplit(match[1].strip("<>"))
                if link.scheme or link.netloc:
                    continue
                raw = unquote(link.path)
                base = root if raw.startswith("/") else path.parent
                target = (base / raw.lstrip("/")).resolve() if raw else path
                location = f"{path.relative_to(root)}:{number}"
                require(
                    target.is_relative_to(root) and target.exists(),
                    f"{location}: missing local link {match[1]}",
                )
                if link.fragment and target.suffix == ".md":
                    if target not in headings:
                        headings[target] = anchors(markdown(target))
                    require(
                        unquote(link.fragment) in headings[target],
                        f"{location}: missing heading for {match[1]}",
                    )


def git(*args: str) -> str:
    return subprocess.check_output(["git", "--no-replace-objects", *args], text=True)


def subjects() -> None:
    event = os.environ.get("GITHUB_EVENT_NAME")
    if event == "pull_request":
        payload = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_bytes())
        require(
            SUBJECT.fullmatch(payload["pull_request"]["title"]) is not None,
            "PR title must be a Conventional Commit, e.g. fix(omp): preserve the original handoff",
        )
    if event == "push" and os.environ.get("GITHUB_REF") == "refs/heads/main":
        ref = "HEAD"
    else:
        candidates = ("refs/heads/main", "refs/remotes/origin/main")
        refs = git("for-each-ref", "--format=%(refname)", *candidates).splitlines()
        ref = next((name for name in candidates if name in refs), "")
        require(
            bool(ref),
            "main history unavailable; use a full checkout with main or origin/main",
        )
    require(
        git("rev-parse", "--is-shallow-repository").strip() == "false",
        "main history check requires a full checkout",
    )
    for line in git("log", "--format=%H%x09%s", ref, "--").splitlines():
        commit, _, subject = line.partition("\t")
        require(
            SUBJECT.fullmatch(subject) is not None,
            f"main commit {commit} lacks a Conventional Commit subject",
        )


if __name__ == "__main__":
    try:
        configuration()
        documentation(Path.cwd())
        subjects()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        sys.exit(f"Development checks: {error}")
