#!/usr/bin/env python3
"""
数据导入脚本 - 将原始数据导入到RAG库中

使用方法:
    # 扫描并导入 data/raw 目录中的所有数据文件
    python scripts/import_data.py

    # 扫描指定目录
    python scripts/import_data.py --dir /path/to/data

    # 导入单个文件
    python scripts/import_data.py --file data/raw/实证论文提取结果.csv --name "实证论文数据集"

    # 查看已导入的数据集
    python scripts/import_data.py --list

    # 搜索数据集
    python scripts/import_data.py --search "企业创新"

    # 查看数据集详情
    python scripts/import_data.py --detail <data_id>

    # 交互模式
    python scripts/import_data.py -i
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from tools.data_storage import DataStorageTool, get_data_storage
from config.config import DATA_STORAGE_CONFIG, RAW_DATA_DIR
from config.logging_config import setup_logger as setup_unified_logger


def setup_logging():
    """配置日志"""
    setup_unified_logger("import_data")


def import_directory(storage: DataStorageTool, directory: str, recursive: bool = True):
    """扫描并导入目录中的数据文件"""
    print(f"\n📂 扫描目录: {directory}")
    print("-" * 50)

    stats = storage.scan_directory(
        directory=directory,
        patterns=["*.csv", "*.xlsx", "*.xls", "*.json", "*.parquet"],
        recursive=recursive,
        auto_extract=True
    )

    print(f"\n📊 导入结果:")
    print(f"   总文件数: {stats['total_files']}")
    print(f"   成功导入: {stats['imported']}")
    print(f"   跳过(已存在): {stats['skipped']}")
    print(f"   错误: {stats['errors']}")

    if stats['imported_ids']:
        print(f"\n✅ 新导入的数据集:")
        for data_id in stats['imported_ids'][:10]:  # 最多显示10个
            item = storage.get_data(data_id)
            if item:
                print(f"   [{data_id}] {item.name}")
                print(f"       路径: {item.file_path}")
                if item.row_count:
                    print(f"       大小: {item.row_count}行 x {item.column_count}列")

        if len(stats['imported_ids']) > 10:
            print(f"   ... 还有 {len(stats['imported_ids']) - 10} 个数据集")

    return stats


def import_single_file(
    storage: DataStorageTool,
    file_path: str,
    name: str = None,
    description: str = None,
    domain: str = None,
    keywords: list = None
):
    """导入单个数据文件"""
    path = Path(file_path)
    if not path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return None

    print(f"\n📄 导入文件: {file_path}")
    print("-" * 50)

    item_data = {
        "name": name or path.stem,
        "description": description or f"从 {path.name} 导入的数据集",
        "file_path": str(path.absolute()),
        "file_type": path.suffix.lstrip('.'),
    }

    if domain:
        item_data["domain"] = domain
    if keywords:
        item_data["keywords"] = keywords

    try:
        data_id = storage.add_data(item_data, auto_extract_summary=True, source="manual_import")

        item = storage.get_data(data_id)
        print(f"\n✅ 导入成功!")
        print(f"   ID: {data_id}")
        print(f"   名称: {item.name}")
        print(f"   路径: {item.file_path}")
        if item.row_count:
            print(f"   大小: {item.row_count}行 x {item.column_count}列")
        if item.columns:
            print(f"   列: {', '.join(item.columns[:10])}")
            if len(item.columns) > 10:
                print(f"        ... 还有 {len(item.columns) - 10} 列")

        return data_id

    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return None


def list_datasets(storage: DataStorageTool, limit: int = 20):
    """列出所有数据集"""
    print(f"\n📚 数据集列表")
    print("-" * 70)

    items = storage.list_all(limit=limit)

    if not items:
        print("   (暂无数据集)")
        return

    for item in items:
        size_info = ""
        if item.row_count:
            size_info = f" ({item.row_count}行 x {item.column_count}列)"

        print(f"\n   [{item.id}] {item.name}{size_info}")
        print(f"       路径: {item.file_path}")
        if item.domain:
            print(f"       领域: {item.domain}")
        if item.keywords:
            print(f"       关键词: {', '.join(item.keywords[:5])}")

    # 统计信息
    stats = storage.get_statistics()
    print(f"\n📊 统计:")
    print(f"   总数据集: {stats['total_count']}")
    if stats['by_type']:
        print(f"   按类型: {stats['by_type']}")
    if stats['by_domain']:
        print(f"   按领域: {stats['by_domain']}")


def search_datasets(storage: DataStorageTool, query: str, n_results: int = 10):
    """搜索数据集"""
    print(f"\n🔍 搜索: {query}")
    print("-" * 70)

    result = storage.search_hybrid(query, n_results=n_results)

    if not result.items:
        print("   未找到匹配的数据集")
        return

    print(f"   找到 {result.total_count} 个匹配")

    for item in result.items:
        size_info = ""
        if item.row_count:
            size_info = f" ({item.row_count}行)"

        print(f"\n   [{item.id}] {item.name}{size_info}")
        print(f"       {item.description[:100]}..." if len(item.description or "") > 100 else f"       {item.description or '无描述'}")
        print(f"       路径: {item.file_path}")


def show_detail(storage: DataStorageTool, data_id: str):
    """显示数据集详情"""
    item = storage.get_data(data_id)

    if not item:
        print(f"❌ 未找到数据集: {data_id}")
        return

    print(f"\n📋 数据集详情: {item.name}")
    print("=" * 70)
    print(f"ID: {item.id}")
    print(f"名称: {item.name}")
    print(f"描述: {item.description}")
    print(f"文件路径: {item.file_path}")
    print(f"文件类型: {item.file_type}")

    if item.row_count:
        print(f"\n📊 数据规模:")
        print(f"   行数: {item.row_count}")
        print(f"   列数: {item.column_count}")

    if item.columns:
        print(f"\n📑 列信息:")
        for i, col in enumerate(item.columns):
            dtype = item.column_types.get(col, "未知")
            missing = item.missing_values.get(col, 0)
            print(f"   {i+1}. {col} ({dtype}) - 缺失: {missing}")

    if item.numeric_summary:
        print(f"\n📈 数值统计 (前3列):")
        for col, stats in list(item.numeric_summary.items())[:3]:
            print(f"   {col}:")
            print(f"      均值: {stats.get('mean', 'N/A'):.4f}, 标准差: {stats.get('std', 'N/A'):.4f}")
            print(f"      最小: {stats.get('min', 'N/A')}, 最大: {stats.get('max', 'N/A')}")

    if item.keywords:
        print(f"\n🏷️ 关键词: {', '.join(item.keywords)}")
    if item.domain:
        print(f"领域: {item.domain}")
    if item.time_range:
        print(f"时间范围: {item.time_range}")
    if item.geographic_scope:
        print(f"地理范围: {item.geographic_scope}")

    print(f"\n⏰ 添加时间: {item.added_at}")
    print(f"来源: {item.source}")


def interactive_mode(storage: DataStorageTool):
    """交互模式"""
    print("\n🎮 数据管理交互模式")
    print("=" * 50)
    print("命令:")
    print("  list [n]        - 列出数据集")
    print("  search <query>  - 搜索数据集")
    print("  detail <id>     - 查看详情")
    print("  import <path>   - 导入文件")
    print("  scan <dir>      - 扫描目录")
    print("  delete <id>     - 删除数据集")
    print("  stats           - 显示统计")
    print("  help            - 显示帮助")
    print("  quit/exit       - 退出")
    print("-" * 50)

    while True:
        try:
            cmd = input("\n> ").strip()
            if not cmd:
                continue

            parts = cmd.split(maxsplit=1)
            action = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            if action in ["quit", "exit", "q"]:
                print("👋 再见!")
                break

            elif action == "list":
                limit = int(args) if args.isdigit() else 20
                list_datasets(storage, limit)

            elif action == "search":
                if args:
                    search_datasets(storage, args)
                else:
                    print("请提供搜索关键词")

            elif action == "detail":
                if args:
                    show_detail(storage, args)
                else:
                    print("请提供数据集ID")

            elif action == "import":
                if args:
                    import_single_file(storage, args)
                else:
                    print("请提供文件路径")

            elif action == "scan":
                directory = args or str(RAW_DATA_DIR)
                import_directory(storage, directory)

            elif action == "delete":
                if args:
                    confirm = input(f"确定删除数据集 {args}? (y/N): ")
                    if confirm.lower() == 'y':
                        storage.delete_data(args)
                        print(f"✅ 已删除: {args}")
                else:
                    print("请提供数据集ID")

            elif action == "stats":
                stats = storage.get_statistics()
                print(f"\n📊 统计信息:")
                print(f"   总数据集: {stats['total_count']}")
                print(f"   按类型: {stats['by_type']}")
                print(f"   按领域: {stats['by_domain']}")
                print(f"   存储路径: {stats['storage_path']}")
                print(f"   RAG可用: {'是' if stats['chroma_available'] else '否'}")

            elif action == "help":
                print("命令: list, search, detail, import, scan, delete, stats, quit")

            else:
                print(f"未知命令: {action}")

        except KeyboardInterrupt:
            print("\n👋 再见!")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")


def main():
    parser = argparse.ArgumentParser(description="数据导入工具")
    parser.add_argument("--dir", "-d", help="扫描并导入指定目录")
    parser.add_argument("--file", "-f", help="导入单个文件")
    parser.add_argument("--name", "-n", help="数据集名称 (配合 --file 使用)")
    parser.add_argument("--description", help="数据集描述")
    parser.add_argument("--domain", help="数据领域")
    parser.add_argument("--keywords", help="关键词，逗号分隔")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有数据集")
    parser.add_argument("--search", "-s", help="搜索数据集")
    parser.add_argument("--detail", help="查看数据集详情")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互模式")
    parser.add_argument("--storage-dir", default=DATA_STORAGE_CONFIG["storage_dir"],
                       help="存储目录")

    args = parser.parse_args()

    setup_logging()

    # 初始化存储工具
    storage = get_data_storage(args.storage_dir)

    # 执行操作
    if args.interactive:
        interactive_mode(storage)

    elif args.list:
        list_datasets(storage)

    elif args.search:
        search_datasets(storage, args.search)

    elif args.detail:
        show_detail(storage, args.detail)

    elif args.file:
        keywords = args.keywords.split(",") if args.keywords else None
        import_single_file(
            storage, args.file,
            name=args.name,
            description=args.description,
            domain=args.domain,
            keywords=keywords
        )

    elif args.dir:
        import_directory(storage, args.dir)

    else:
        # 默认扫描 data/raw 目录
        print("🚀 数据导入工具")
        print(f"默认扫描目录: {RAW_DATA_DIR}")

        if RAW_DATA_DIR.exists():
            import_directory(storage, str(RAW_DATA_DIR))
        else:
            print(f"⚠️ 目录不存在: {RAW_DATA_DIR}")
            print("使用 --help 查看更多选项")


if __name__ == "__main__":
    main()
