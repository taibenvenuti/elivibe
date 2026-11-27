import hashlib

import pytest

from dev.package import skill_digest


@pytest.fixture
def skill(tmp_path):
    path = tmp_path / "skills/elivibe/SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "---\nname: elivibe\ndescription: A concise project handoff\n"
        "disable-model-invocation: true\n---\n\n# Handoff\n",
        encoding="utf-8",
    )
    return path


def test_package_reports_current_bytes(skill, tmp_path):
    assert skill_digest(tmp_path) == hashlib.sha256(skill.read_bytes()).hexdigest()


@pytest.mark.parametrize("layer", ["root", "directory", "file"])
def test_package_rejects_symlink_escape(skill, tmp_path, layer):
    path = {"root": skill.parents[1], "directory": skill.parent, "file": skill}[layer]
    escape = tmp_path / "outside"
    path.rename(escape)
    path.symlink_to(escape, target_is_directory=escape.is_dir())
    with pytest.raises(ValueError, match="invalid skill"):
        skill_digest(tmp_path)


@pytest.mark.parametrize("where", ["sibling", "child"])
def test_package_rejects_extras(skill, tmp_path, where):
    directory = skill.parents[1] if where == "sibling" else skill.parent
    (directory / "unexpected").touch()
    with pytest.raises(ValueError, match="unexpected skill tree"):
        skill_digest(tmp_path)


def test_package_rejects_executable_skill(skill, tmp_path):
    skill.chmod(0o755)
    with pytest.raises(ValueError, match="invalid skill file mode"):
        skill_digest(tmp_path)


@pytest.mark.parametrize(
    ("old", "new", "error"),
    [
        (b"name: elivibe", b"name: bogus", "invalid native skill metadata"),
        (b"A concise project handoff", b" ", "invalid native skill metadata"),
        (b"disable-model-invocation: true", b"", "invalid native skill metadata"),
        (b"# Handoff\n", b"", "empty skill body"),
    ],
)
def test_package_rejects_invalid_content(skill, tmp_path, old, new, error):
    skill.write_bytes(skill.read_bytes().replace(old, new))
    with pytest.raises(ValueError, match=error):
        skill_digest(tmp_path)
