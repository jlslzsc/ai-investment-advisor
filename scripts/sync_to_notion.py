"""
批量同步 Markdown 文件到 Notion
使用 md2notionpage 包
支持哈希检查，跳过未变化的文件
"""
import os
import sys
import subprocess
import hashlib
import json
from pathlib import Path
from datetime import datetime

# 导入配置
from api_config import NOTION_API_KEY, NOTION_PAGE_ID

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
STOCK_INFO_DIR = PROJECT_ROOT / "股市信息"

# 要同步的目录（按优先级排序）
SYNC_DIRS = [
    "Config",      # 配置文件
    "Daily",       # 每日简报
    "Brief",       # 持仓分析
    "Analysis",    # 个股分析
    "Scan",        # 市场扫描
    "Records",     # 交易记录
    "Committee",   # 投委会
]

# 哈希缓存文件
HASH_CACHE_FILE = PROJECT_ROOT / ".notion_sync_cache.json"

def load_hash_cache() -> dict:
    """加载哈希缓存"""
    if HASH_CACHE_FILE.exists():
        try:
            return json.loads(HASH_CACHE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_hash_cache(cache: dict):
    """保存哈希缓存"""
    HASH_CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")

def file_hash(path: Path) -> str:
    """计算文件内容的 MD5 哈希"""
    return hashlib.md5(path.read_bytes()).hexdigest()

def get_md_files():
    """获取所有需要同步的 markdown 文件"""
    files = []

    for dir_name in SYNC_DIRS:
        dir_path = STOCK_INFO_DIR / dir_name
        if dir_path.exists():
            for md_file in dir_path.glob("**/*.md"):
                # 跳过模板文件
                if "template" in md_file.name.lower():
                    continue
                files.append(md_file)

    return files

def sync_file(md_path: Path) -> dict:
    """同步单个文件到 Notion"""
    # 生成标题：目录名/文件名
    relative_path = md_path.relative_to(STOCK_INFO_DIR)
    title = f"{relative_path.parent.name}/{md_path.stem}"

    # 设置环境变量
    env = os.environ.copy()
    env["NOTION_API_KEY"] = NOTION_API_KEY

    try:
        result = subprocess.run(
            [
                "python3", "-m", "md2notionpage",
                str(md_path),
                NOTION_PAGE_ID,
                "--title", title
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return {"file": str(md_path), "status": "success", "title": title}
        else:
            return {"file": str(md_path), "status": "failed", "error": result.stderr}

    except subprocess.TimeoutExpired:
        return {"file": str(md_path), "status": "timeout"}
    except Exception as e:
        return {"file": str(md_path), "status": "error", "error": str(e)}

def main():
    print(f"=== Notion 同步工具 ===")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标页面: {NOTION_PAGE_ID}")
    print()

    # 加载哈希缓存
    hash_cache = load_hash_cache()

    files = get_md_files()
    print(f"找到 {len(files)} 个 markdown 文件")
    print()

    success = []
    failed = []
    skipped = []

    for i, md_file in enumerate(files, 1):
        file_key = str(md_file.relative_to(PROJECT_ROOT))
        current_hash = file_hash(md_file)

        # 检查哈希是否变化
        if hash_cache.get(file_key) == current_hash:
            print(f"[{i}/{len(files)}] 跳过: {md_file.name} (未变化)")
            skipped.append({"file": str(md_file), "status": "skipped"})
            continue

        print(f"[{i}/{len(files)}] 同步: {md_file.name}...", end=" ")
        result = sync_file(md_file)

        if result["status"] == "success":
            print("✓")
            success.append(result)
            # 更新哈希缓存
            hash_cache[file_key] = current_hash
        else:
            print(f"✗ ({result.get('error', result['status'])})")
            failed.append(result)

    # 保存哈希缓存
    save_hash_cache(hash_cache)

    print()
    print(f"=== 同步完成 ===")
    print(f"成功: {len(success)}")
    print(f"跳过: {len(skipped)} (未变化)")
    print(f"失败: {len(failed)}")

    if failed:
        print("\n失败文件:")
        for f in failed:
            print(f"  - {f['file']}: {f.get('error', f['status'])}")

if __name__ == "__main__":
    main()
