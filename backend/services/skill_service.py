from pathlib import Path


SKILLS_DIR = Path(__file__).resolve().parents[1] / "skills"


def load_skill(skill_name: str) -> str:
    skill_path = SKILLS_DIR / f"{skill_name}.skill.md"
    if not skill_path.exists():
        raise FileNotFoundError(f"Skill file not found: {skill_path}")

    # prompt 内容统一放在 skills 文件中，避免业务代码写死大段提示词。
    return skill_path.read_text(encoding="utf-8")
