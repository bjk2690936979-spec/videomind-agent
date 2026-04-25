from pathlib import Path

import pytest

from backend.services import skill_service


def test_list_skills_returns_skill_files() -> None:
    skills = skill_service.list_skills()

    assert "summary" in skills
    assert "quiz" in skills
    assert "context_compress" in skills


def test_load_skill_reads_existing_skill() -> None:
    content = skill_service.load_skill("summary")

    assert "# Summary Skill" in content
    assert "## Output" in content


def test_load_missing_skill_raises_clear_error() -> None:
    with pytest.raises(FileNotFoundError, match="Skill file not found"):
        skill_service.load_skill("not_exists")


def test_render_skill_replaces_variables(tmp_path, monkeypatch) -> None:
    skill_file = Path(tmp_path, "demo.skill.md")
    skill_file.write_text("学习材料：{{text}}\n总结：{{summary}}", encoding="utf-8")
    monkeypatch.setattr(skill_service, "SKILLS_DIR", tmp_path)

    rendered = skill_service.render_skill(
        "demo",
        {
            "text": "FastAPI 文本",
            "summary": "一句话总结",
        },
    )

    assert rendered == "学习材料：FastAPI 文本\n总结：一句话总结"
