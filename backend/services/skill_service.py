from pathlib import Path
from typing import Dict, List


SKILLS_DIR = Path(__file__).resolve().parents[1] / "skills"


def _skill_path(skill_name: str) -> Path:
    return SKILLS_DIR / f"{skill_name}.skill.md"


def load_skill(skill_name: str) -> str:
    skill_path = _skill_path(skill_name)
    if not skill_path.exists():
        raise FileNotFoundError(f"Skill file not found: {skill_path}")

    # prompt 内容统一放在 skills 文件中，避免业务代码写死大段提示词。
    return skill_path.read_text(encoding="utf-8")


def list_skills() -> List[str]:
    if not SKILLS_DIR.exists():
        raise FileNotFoundError(f"Skills directory not found: {SKILLS_DIR}")
    return sorted(path.name.removesuffix(".skill.md") for path in SKILLS_DIR.glob("*.skill.md"))


def render_skill(skill_name: str, variables: Dict[str, object]) -> str:
    content = load_skill(skill_name)
    rendered = content
    for key, value in variables.items():
        # 第一版只做简单占位符替换，避免引入模板引擎复杂度。
        rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
    return rendered
