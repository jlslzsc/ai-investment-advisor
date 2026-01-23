"""Skills 路由"""
from fastapi import APIRouter
from services.skill_parser import SkillParser, DEFAULT_SKILLS
from config import settings

router = APIRouter()


@router.get("/api/skills")
async def get_skills():
    """
    获取所有可用的 Skills

    Returns:
        {
            "skills": [
                {
                    "name": "brief",
                    "command": "/brief",
                    "description": "生成每日投资简报",
                    "triggers": ["/brief", "简报", "今日市场"],
                    "example": "/brief"
                },
                ...
            ]
        }
    """
    parser = SkillParser(settings.project_path)
    skills = parser.get_all_skills()

    # 如果解析失败，使用默认 skills
    if not skills:
        skills = DEFAULT_SKILLS

    return {"skills": skills}


@router.get("/api/skills/{skill_name}")
async def get_skill(skill_name: str):
    """
    获取单个 Skill 的详细信息

    Args:
        skill_name: Skill 名称，如 "brief", "scan"

    Returns:
        Skill 详情或 404
    """
    parser = SkillParser(settings.project_path)
    skills = parser.get_all_skills()

    if not skills:
        skills = DEFAULT_SKILLS

    for skill in skills:
        if skill['name'] == skill_name:
            return skill

    return {"error": "Skill not found"}, 404
