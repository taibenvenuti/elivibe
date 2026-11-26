import check_dev
import pytest


def test_commit_subjects():
    assert check_dev.SUBJECT.fullmatch("fix(omp)!: preserve handoff")
    assert not check_dev.SUBJECT.fullmatch("Merge pull request #2")
    assert not check_dev.SUBJECT.fullmatch("fix: \nsecond line")


def test_docs_validate_links_anchors_and_shell_syntax(tmp_path, monkeypatch):
    monkeypatch.setattr(check_dev, "DOCS", ("README.md",))
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text("# First (step)\n## First step\n", encoding="utf-8")
    readme = tmp_path / "README.md"
    readme.write_text(
        "[Go](docs/guide.md#first-step-1)\n```sh\nprintf '%s\\n' ok\n```\n",
        encoding="utf-8",
    )
    check_dev.documentation(tmp_path)
    readme.write_text("[Go](docs/guide.md#missing)\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing heading"):
        check_dev.documentation(tmp_path)
    readme.write_text("```sh\nif true; then\n```\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid shell example"):
        check_dev.documentation(tmp_path)
