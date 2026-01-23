"""Notion 同步服务"""
import os
import re
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False

logger = logging.getLogger(__name__)


class NotionSync:
    """Notion 文档同步服务"""

    # 哈希缓存文件路径（相对于项目根目录）
    HASH_CACHE_FILE = ".notion_sync_cache.json"

    def __init__(self, token: str, parent_page_id: str):
        """
        初始化 Notion 同步服务

        Args:
            token: Notion API Token (Integration Token)
            parent_page_id: 父页面 ID，所有文档将同步到此页面下
        """
        if not NOTION_AVAILABLE:
            raise ImportError("notion-client 未安装，请运行: pip install notion-client")

        self.token = token
        self.parent_page_id = parent_page_id.replace("-", "")
        self.client = Client(auth=token)
        self._page_cache = {}  # 缓存已创建的页面
        self._hash_cache = self._load_hash_cache()

    def _get_cache_path(self) -> Path:
        """获取哈希缓存文件路径"""
        # 从当前文件向上找到项目根目录
        current = Path(__file__).parent.parent.parent
        return current / self.HASH_CACHE_FILE

    def _load_hash_cache(self) -> dict:
        """加载哈希缓存"""
        cache_path = self._get_cache_path()
        if cache_path.exists():
            try:
                return json.loads(cache_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_hash_cache(self):
        """保存哈希缓存"""
        cache_path = self._get_cache_path()
        cache_path.write_text(json.dumps(self._hash_cache, indent=2, ensure_ascii=False), encoding="utf-8")

    def _file_hash(self, path: Path) -> str:
        """计算文件内容的 MD5 哈希"""
        return hashlib.md5(path.read_bytes()).hexdigest()

    def _is_file_changed(self, local_path: str) -> bool:
        """检查文件是否有变化"""
        path = Path(local_path)
        current_hash = self._file_hash(path)
        cached_hash = self._hash_cache.get(local_path)
        return current_hash != cached_hash

    def _update_file_hash(self, local_path: str):
        """更新文件哈希缓存"""
        path = Path(local_path)
        self._hash_cache[local_path] = self._file_hash(path)
        self._save_hash_cache()

    def _md_to_notion_blocks(self, md_content: str) -> List[dict]:
        """将 Markdown 转换为 Notion blocks"""
        blocks = []
        lines = md_content.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i]

            # 标题
            if line.startswith('# '):
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {"rich_text": [{"type": "text", "text": {"content": line[2:].strip()}}]}
                })
            elif line.startswith('## '):
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"type": "text", "text": {"content": line[3:].strip()}}]}
                })
            elif line.startswith('### '):
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {"rich_text": [{"type": "text", "text": {"content": line[4:].strip()}}]}
                })
            # 列表项
            elif line.startswith('- '):
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": line[2:].strip()}}]}
                })
            elif re.match(r'^\d+\. ', line):
                content = re.sub(r'^\d+\. ', '', line).strip()
                blocks.append({
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {"rich_text": [{"type": "text", "text": {"content": content}}]}
                })
            # 引用
            elif line.startswith('> '):
                blocks.append({
                    "object": "block",
                    "type": "quote",
                    "quote": {"rich_text": [{"type": "text", "text": {"content": line[2:].strip()}}]}
                })
            # 代码块
            elif line.startswith('```'):
                code_lines = []
                lang = line[3:].strip() or "plain text"
                # 映射常见语言
                lang_map = {
                    "python": "python",
                    "py": "python",
                    "javascript": "javascript",
                    "js": "javascript",
                    "typescript": "typescript",
                    "ts": "typescript",
                    "bash": "bash",
                    "sh": "bash",
                    "shell": "bash",
                    "json": "json",
                    "markdown": "markdown",
                    "md": "markdown",
                    "sql": "sql",
                    "html": "html",
                    "css": "css",
                }
                lang = lang_map.get(lang.lower(), "plain text")

                i += 1
                while i < len(lines) and not lines[i].startswith('```'):
                    code_lines.append(lines[i])
                    i += 1

                code_content = '\n'.join(code_lines)
                if code_content:
                    blocks.append({
                        "object": "block",
                        "type": "code",
                        "code": {
                            "rich_text": [{"type": "text", "text": {"content": code_content[:2000]}}],
                            "language": lang
                        }
                    })
            # 分隔线
            elif line.strip() == '---':
                blocks.append({
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                })
            # 表格（简化处理，转为代码块）
            elif line.startswith('|'):
                table_lines = [line]
                i += 1
                while i < len(lines) and lines[i].startswith('|'):
                    table_lines.append(lines[i])
                    i += 1
                i -= 1  # 回退一行

                blocks.append({
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [{"type": "text", "text": {"content": '\n'.join(table_lines)}}],
                        "language": "markdown"
                    }
                })
            # 普通段落
            elif line.strip():
                # 处理加粗和斜体
                text = line.strip()
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}}]}
                })

            i += 1

        # Notion API 限制每次最多100个blocks
        return blocks[:100]

    # 需要覆盖更新的目录（删除后重建）
    OVERWRITE_DIRS = {"Config", "Records"}

    async def sync_file(self, local_path: str, title: str = None, force: bool = False) -> Dict:
        """
        同步单个文件到 Notion

        Args:
            local_path: 本地文件路径
            title: 文档标题，默认使用 "目录/文件名" 格式
            force: 强制同步，忽略哈希检查

        Returns:
            同步结果字典
        """
        if not os.path.exists(local_path):
            return {
                'local': local_path,
                'status': 'failed',
                'message': '文件不存在'
            }

        # 检查文件是否有变化
        if not force and not self._is_file_changed(local_path):
            logger.info(f"Skipping {local_path} (unchanged)")
            return {
                'local': local_path,
                'status': 'skipped',
                'message': '文件未变化，跳过同步'
            }

        try:
            path = Path(local_path)
            content = path.read_text(encoding='utf-8')

            # 生成标题并判断目录类型
            dir_name = None
            if not title:
                # 尝试从路径中提取目录名
                parts = path.parts
                if '股市信息' in parts:
                    idx = parts.index('股市信息')
                    if idx + 1 < len(parts):
                        dir_name = parts[idx + 1]
                        title = f"{dir_name}/{path.stem}"
                    else:
                        title = path.stem
                else:
                    title = path.stem
            else:
                # 从 title 中提取目录名
                if '/' in title:
                    dir_name = title.split('/')[0]

            # 判断是否需要覆盖更新
            should_overwrite = dir_name in self.OVERWRITE_DIRS

            logger.info(f"Syncing {local_path} as '{title}' (overwrite={should_overwrite})")

            # 检查是否已存在同名页面
            existing_page_id = await self._find_page_by_title(title)

            if existing_page_id:
                if should_overwrite:
                    # Config/Records: 删除后重建
                    await self._delete_page(existing_page_id)
                    if title in self._page_cache:
                        del self._page_cache[title]
                else:
                    # 其他目录: 已存在则跳过
                    logger.info(f"Skipping {local_path} (already exists in Notion)")
                    # 更新哈希缓存，下次不再检查
                    self._update_file_hash(local_path)
                    return {
                        'local': local_path,
                        'status': 'skipped',
                        'message': 'Notion 中已存在，跳过同步'
                    }

            blocks = self._md_to_notion_blocks(content)

            # 创建新页面
            new_page = self.client.pages.create(
                parent={"page_id": self.parent_page_id},
                properties={
                    "title": [{"type": "text", "text": {"content": title}}]
                },
                children=blocks
            )
            page_url = new_page.get("url", "")
            action = "updated" if (existing_page_id and should_overwrite) else "created"

            # 同步成功后更新哈希缓存
            self._update_file_hash(local_path)

            return {
                'local': local_path,
                'notion_url': page_url,
                'title': title,
                'status': 'success',
                'message': f'文档已{"更新" if action == "updated" else "创建"}'
            }

        except Exception as e:
            logger.error(f"Sync error for {local_path}: {e}")
            return {
                'local': local_path,
                'status': 'failed',
                'message': str(e)
            }

    async def sync_directory(self, local_dir: str, pattern: str = "*.md", force: bool = False) -> Dict:
        """
        同步整个目录到 Notion

        Args:
            local_dir: 本地目录路径
            pattern: 文件匹配模式
            force: 强制同步，忽略哈希检查

        Returns:
            同步结果汇总
        """
        synced = []
        failed = []
        skipped = []

        for path in Path(local_dir).glob(f"**/{pattern}"):
            # 跳过模板文件
            if "template" in path.name.lower():
                continue

            result = await self.sync_file(str(path), force=force)
            if result['status'] == 'success':
                synced.append(result)
            elif result['status'] == 'skipped':
                skipped.append(result)
            else:
                failed.append(result)

        return {
            'synced': synced,
            'skipped': skipped,
            'failed': failed,
            'status': 'ok' if not failed else 'partial'
        }

    async def _find_page_by_title(self, title: str) -> Optional[str]:
        """查找同名页面"""
        if title in self._page_cache:
            return self._page_cache[title]

        try:
            results = self.client.search(
                query=title,
                filter={"property": "object", "value": "page"}
            )

            for page in results.get("results", []):
                props = page.get("properties", {})
                for key, val in props.items():
                    if val.get("type") == "title":
                        title_arr = val.get("title", [])
                        if title_arr:
                            page_title = title_arr[0].get("plain_text", "")
                            if page_title == title:
                                page_id = page.get("id")
                                self._page_cache[title] = page_id
                                return page_id
        except Exception as e:
            logger.warning(f"Search failed: {e}")

        return None

    async def _delete_page(self, page_id: str):
        """删除整个页面（归档）"""
        try:
            # Notion API 通过设置 archived=True 来删除页面
            self.client.pages.update(page_id=page_id, archived=True)
            logger.info(f"Deleted page {page_id}")
        except Exception as e:
            logger.warning(f"Delete page failed: {e}")
            raise

    async def test_connection(self) -> Dict:
        """测试 Notion 连接"""
        try:
            # 测试获取用户信息
            me = self.client.users.me()

            # 测试获取父页面
            page = self.client.pages.retrieve(page_id=self.parent_page_id)

            # 获取页面标题
            title = "无标题"
            props = page.get("properties", {})
            for key, val in props.items():
                if val.get("type") == "title":
                    title_arr = val.get("title", [])
                    if title_arr:
                        title = title_arr[0].get("plain_text", "无标题")
                    break

            return {
                'status': 'ok',
                'integration_name': me.get('name', me.get('type')),
                'page_title': title,
                'page_id': self.parent_page_id
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }


# ========== 单元测试 ==========
async def test_notion_sync():
    """测试 Notion 同步"""
    import asyncio

    token = os.environ.get('NOTION_API_KEY', '')
    page_id = os.environ.get('NOTION_PAGE_ID', '')

    if not token or not page_id:
        print("请设置 NOTION_API_KEY 和 NOTION_PAGE_ID 环境变量")
        return

    sync = NotionSync(token, page_id)

    # 测试连接
    print("Testing connection...")
    result = await sync.test_connection()
    print(f"Connection result: {result}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_notion_sync())
