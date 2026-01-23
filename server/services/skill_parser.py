"""Skill 解析服务"""
import os
import re
import yaml
from typing import List, Dict, Optional
from pathlib import Path


class SkillParser:
    """解析 .claude/skills 目录下的 SKILL.md 文件"""

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.skills_dir = os.path.join(project_path, ".claude", "skills")

    def get_all_skills(self) -> List[Dict]:
        """获取所有可用的 Skills"""
        skills = []

        if not os.path.exists(self.skills_dir):
            return skills

        for skill_name in os.listdir(self.skills_dir):
            skill_dir = os.path.join(self.skills_dir, skill_name)
            skill_file = os.path.join(skill_dir, "SKILL.md")

            if os.path.isdir(skill_dir) and os.path.exists(skill_file):
                skill_info = self._parse_skill_file(skill_file, skill_name)
                if skill_info:
                    skills.append(skill_info)

        return sorted(skills, key=lambda x: x['name'])

    def _parse_skill_file(self, file_path: str, skill_name: str) -> Optional[Dict]:
        """解析单个 SKILL.md 文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 解析 YAML 前言
            frontmatter = self._extract_frontmatter(content)

            if not frontmatter:
                return None

            # 只返回 user-invocable 的 skills
            if not frontmatter.get('user-invocable', False):
                return None

            # 提取触发词
            triggers = self._extract_triggers(content, skill_name)

            # 提取示例
            example = self._extract_example(content, skill_name)

            return {
                'name': frontmatter.get('name', skill_name),
                'command': f"/{skill_name}",
                'description': frontmatter.get('description', ''),
                'triggers': triggers,
                'example': example
            }

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None

    def _extract_frontmatter(self, content: str) -> Optional[Dict]:
        """提取 YAML 前言"""
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if match:
            try:
                return yaml.safe_load(match.group(1))
            except yaml.YAMLError:
                return None
        return None

    def _extract_triggers(self, content: str, skill_name: str) -> List[str]:
        """从描述中提取触发词"""
        triggers = [f"/{skill_name}"]

        # 从 description 中提取引号内的触发词
        # 例如: 当用户说"简报"、"今日市场"、"持仓分析"时使用此skill
        trigger_pattern = r'["「]([^"」]+)["」]'
        matches = re.findall(trigger_pattern, content[:500])

        for match in matches:
            if match and match not in triggers and len(match) < 20:
                triggers.append(match)

        return triggers[:6]  # 最多返回 6 个触发词

    def _extract_example(self, content: str, skill_name: str) -> str:
        """提取使用示例"""
        # 查找代码块中的示例
        code_pattern = rf'/({skill_name}[^\n`]*)'
        match = re.search(code_pattern, content)
        if match:
            return f"/{match.group(1).strip()}"

        return f"/{skill_name}"


# 预定义的 Skills 信息（作为备用）
DEFAULT_SKILLS = [
    {
        'name': 'brief',
        'command': '/brief',
        'description': '生成每日投资简报',
        'triggers': ['/brief', '简报', '今日市场', '持仓分析', '操作建议'],
        'example': '/brief'
    },
    {
        'name': 'scan',
        'command': '/scan',
        'description': '市场扫描与标的推荐',
        'triggers': ['/scan', '有什么机会', '推荐', '扫描市场', '找标的'],
        'example': '/scan AI'
    },
    {
        'name': 'analyze',
        'command': '/analyze',
        'description': '个股深度分析',
        'triggers': ['/analyze', '分析', '看看', '怎么样', '值得买吗'],
        'example': '/analyze 00700'
    },
    {
        'name': 'trade',
        'command': '/trade',
        'description': '记录交易操作',
        'triggers': ['/trade', '买了', '卖了', '加仓', '减仓', '清仓'],
        'example': '/trade 买了002565 15.33元 300股'
    },
    {
        'name': 'review',
        'command': '/review',
        'description': '周期性复盘分析',
        'triggers': ['/review', '复盘', '回顾', '验证', '总结'],
        'example': '/review week'
    },
    {
        'name': 'committee',
        'command': '/committee',
        'description': '多模型投资委员会',
        'triggers': ['/committee', '开会', '投资委员会', '多模型分析'],
        'example': '/committee'
    }
]


# ========== 单元测试 ==========
def test_skill_parser():
    """测试 Skill 解析器"""
    import os

    project_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    parser = SkillParser(project_path)

    print(f"Project path: {project_path}")
    print(f"Skills dir: {parser.skills_dir}")
    print()

    skills = parser.get_all_skills()
    print(f"Found {len(skills)} skills:\n")

    for skill in skills:
        print(f"Name: {skill['name']}")
        print(f"  Command: {skill['command']}")
        print(f"  Description: {skill['description'][:50]}...")
        print(f"  Triggers: {skill['triggers']}")
        print(f"  Example: {skill['example']}")
        print()


if __name__ == "__main__":
    test_skill_parser()
