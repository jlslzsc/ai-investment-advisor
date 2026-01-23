"""语雀同步服务"""
import os
import httpx
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class YuqueSync:
    """语雀文档同步服务"""

    def __init__(self, token: str, namespace: str):
        """
        初始化语雀同步服务

        Args:
            token: 语雀 API Token
            namespace: 知识库路径，如 "username/repo"
        """
        self.token = token
        self.namespace = namespace
        self.base_url = "https://www.yuque.com/api/v2"
        self.headers = {
            "X-Auth-Token": token,
            "Content-Type": "application/json"
        }

    async def sync_file(self, local_path: str, title: str = None) -> Dict:
        """
        同步单个文件到语雀

        Args:
            local_path: 本地文件路径
            title: 文档标题，默认使用文件名

        Returns:
            同步结果字典
        """
        if not os.path.exists(local_path):
            return {
                'local': local_path,
                'status': 'failed',
                'message': '文件不存在'
            }

        try:
            content = Path(local_path).read_text(encoding='utf-8')
            title = title or Path(local_path).stem
            slug = self._path_to_slug(local_path)

            logger.info(f"Syncing {local_path} as {slug}")

            # 检查是否已存在
            existing = await self._get_doc(slug)

            async with httpx.AsyncClient(timeout=30.0) as client:
                if existing:
                    # 更新已有文档
                    resp = await client.put(
                        f"{self.base_url}/repos/{self.namespace}/docs/{slug}",
                        headers=self.headers,
                        json={
                            "title": title,
                            "body": content,
                            "public": 0  # 私密
                        }
                    )
                    action = "updated"
                else:
                    # 创建新文档
                    resp = await client.post(
                        f"{self.base_url}/repos/{self.namespace}/docs",
                        headers=self.headers,
                        json={
                            "title": title,
                            "slug": slug,
                            "body": content,
                            "public": 0
                        }
                    )
                    action = "created"

                if resp.status_code in [200, 201]:
                    data = resp.json().get('data', {})
                    return {
                        'local': local_path,
                        'yuque_url': f"https://www.yuque.com/{self.namespace}/{slug}",
                        'status': 'success',
                        'message': f'文档已{"更新" if action == "updated" else "创建"}'
                    }
                else:
                    error_msg = resp.json().get('message', resp.text)
                    logger.error(f"Sync failed: {error_msg}")
                    return {
                        'local': local_path,
                        'status': 'failed',
                        'message': error_msg
                    }

        except Exception as e:
            logger.error(f"Sync error: {e}")
            return {
                'local': local_path,
                'status': 'failed',
                'message': str(e)
            }

    async def sync_directory(self, local_dir: str, pattern: str = "*.md") -> Dict:
        """
        同步整个目录到语雀

        Args:
            local_dir: 本地目录路径
            pattern: 文件匹配模式

        Returns:
            同步结果汇总
        """
        synced = []
        failed = []

        for path in Path(local_dir).glob(f"**/{pattern}"):
            result = await self.sync_file(str(path))
            if result['status'] == 'success':
                synced.append(result)
            else:
                failed.append(result)

        return {
            'synced': synced,
            'failed': failed,
            'status': 'ok' if not failed else 'partial'
        }

    async def _get_doc(self, slug: str) -> Optional[Dict]:
        """检查文档是否存在"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.base_url}/repos/{self.namespace}/docs/{slug}",
                    headers=self.headers
                )
                if resp.status_code == 200:
                    return resp.json().get('data')
        except Exception:
            pass
        return None

    def _path_to_slug(self, path: str) -> str:
        """将文件路径转换为语雀 slug"""
        stem = Path(path).stem
        # 语雀 slug 规则：小写字母、数字、连字符
        slug = stem.lower()
        slug = slug.replace(' ', '-')
        slug = slug.replace('_', '-')
        # 移除中文和特殊字符，用拼音或日期保留
        # 对于日期格式的文件名（如 2026-01-22-Brief），保持不变
        return slug

    async def test_connection(self) -> Dict:
        """测试语雀连接"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.base_url}/repos/{self.namespace}",
                    headers=self.headers
                )
                if resp.status_code == 200:
                    data = resp.json().get('data', {})
                    return {
                        'status': 'ok',
                        'repo_name': data.get('name'),
                        'repo_id': data.get('id')
                    }
                else:
                    return {
                        'status': 'error',
                        'message': resp.json().get('message', '连接失败')
                    }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }


# ========== 单元测试 ==========
async def test_yuque_sync():
    """测试语雀同步（需要配置有效的 token）"""
    import asyncio

    # 测试配置（需要替换为真实值）
    token = os.environ.get('YUQUE_TOKEN', '')
    namespace = os.environ.get('YUQUE_NAMESPACE', '')

    if not token or not namespace:
        print("请设置 YUQUE_TOKEN 和 YUQUE_NAMESPACE 环境变量")
        return

    sync = YuqueSync(token, namespace)

    # 测试连接
    print("Testing connection...")
    result = await sync.test_connection()
    print(f"Connection result: {result}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_yuque_sync())
