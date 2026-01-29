"""
文献数据库查看工具

查看向量数据库的当前状态、统计信息和搜索测试

使用方法:
    python scripts/view_database.py              # 查看概览
    python scripts/view_database.py --search "数字化转型"  # 语义搜索
    python scripts/view_database.py --keyword "DID"        # 关键词搜索
    python scripts/view_database.py --list 20              # 列出最近20篇
    python scripts/view_database.py --detail <id>          # 查看详情
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.literature_storage import LiteratureStorageTool
from loguru import logger
from config.logging_config import setup_logger

# 配置日志
LOG_FILE = setup_logger("view_database")


def print_separator(title: str = "", char: str = "=", width: int = 70):
    """打印分隔线"""
    if title:
        padding = (width - len(title) - 2) // 2
        print(f"{char * padding} {title} {char * padding}")
    else:
        print(char * width)


def format_truncate(text: str, max_len: int = 60) -> str:
    """截断文本"""
    if not text:
        return "N/A"
    text = str(text).replace("\n", " ").strip()
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


def show_overview(storage: LiteratureStorageTool):
    """显示数据库概览"""
    stats = storage.get_statistics()

    print_separator("文献数据库概览")
    print(f"存储路径: {stats.get('storage_path', 'N/A')}")
    print(f"总文献数: {stats.get('total_count', 0)}")
    print(f"向量数据库: {'✓ 已启用' if stats.get('chroma_available') else '✗ 未启用'}")
    print(f"嵌入模型: {stats.get('embedding_model', 'N/A')}")

    # 按年份统计
    by_year = stats.get("by_year", {})
    if by_year:
        print_separator("按年份统计", "-")
        sorted_years = sorted(by_year.items(), key=lambda x: x[0], reverse=True)
        for year, count in sorted_years[:10]:
            bar = "█" * min(count // 5, 30)
            print(f"  {year}: {count:4d} {bar}")
        if len(sorted_years) > 10:
            print(f"  ... 还有 {len(sorted_years) - 10} 个年份")

    # 按期刊统计
    by_journal = stats.get("by_journal", {})
    if by_journal:
        print_separator("按期刊/来源统计 (Top 10)", "-")
        sorted_journals = sorted(by_journal.items(), key=lambda x: x[1], reverse=True)
        for journal, count in sorted_journals[:10]:
            print(f"  {format_truncate(journal, 40):42s} : {count:4d}")

    print_separator()


def show_list(storage: LiteratureStorageTool, limit: int = 20):
    """列出文献"""
    items = storage.list_all(sort_by="added_at", descending=True, limit=limit)

    print_separator(f"最近添加的 {len(items)} 篇文献")
    print(f"{'ID':<14} {'标题':<45} {'方法':<15}")
    print("-" * 70)

    for item in items:
        title = format_truncate(item.title, 43)
        method = format_truncate(item.identification_strategy or "N/A", 13)
        print(f"{item.id:<14} {title:<45} {method:<15}")

    print_separator()


def show_detail(storage: LiteratureStorageTool, item_id: str):
    """显示文献详情"""
    item = storage.get_literature(item_id)

    if not item:
        print(f"未找到文献: {item_id}")
        return

    print_separator(f"文献详情: {item_id}")
    print(f"标题: {item.title}")
    print(f"作者: {item.authors}")
    print(f"年份: {item.year}")
    print(f"期刊: {item.journal or 'N/A'}")
    print(f"来源: {item.source}")
    print(f"添加时间: {item.added_at}")

    if item.tags:
        print(f"标签: {', '.join(item.tags)}")

    print_separator("研究内容", "-")
    print(f"摘要/研究问题:\n  {item.abstract or 'N/A'}")
    print(f"\n自变量X定义:\n  {item.variable_x_definition or 'N/A'}")
    print(f"\n因变量Y定义:\n  {item.variable_y_definition or 'N/A'}")
    print(f"\n识别策略/计量方法:\n  {item.identification_strategy or 'N/A'}")

    if item.core_conclusion:
        print(f"\n核心结论:\n  {item.core_conclusion}")

    if item.notes:
        print(f"\n备注:\n  {item.notes}")

    print_separator()


def do_search(storage: LiteratureStorageTool, query: str, search_type: str = "semantic", n_results: int = 10):
    """执行搜索"""
    print_separator(f"{search_type.upper()} 搜索: '{query}'")

    if search_type == "semantic":
        results = storage.search_semantic(query, n_results=n_results)
    elif search_type == "keyword":
        results = storage.search_keyword(query, n_results=n_results)
    else:
        results = storage.search_hybrid(query, n_results=n_results)

    print(f"找到 {results.total_count} 条结果\n")

    for i, item in enumerate(results.items, 1):
        print(f"[{i}] {item.title}")
        print(f"    ID: {item.id}")
        if item.variable_x_definition:
            print(f"    X: {format_truncate(item.variable_x_definition, 55)}")
        if item.variable_y_definition:
            print(f"    Y: {format_truncate(item.variable_y_definition, 55)}")
        if item.identification_strategy:
            print(f"    方法: {format_truncate(item.identification_strategy, 50)}")
        print()

    print_separator()


def interactive_mode(storage: LiteratureStorageTool):
    """交互模式"""
    print_separator("交互模式")
    print("命令:")
    print("  s <query>  - 语义搜索")
    print("  k <query>  - 关键词搜索")
    print("  l [n]      - 列出文献 (默认20篇)")
    print("  d <id>     - 查看详情")
    print("  o          - 显示概览")
    print("  q          - 退出")
    print_separator()

    while True:
        try:
            cmd = input("\n> ").strip()
            if not cmd:
                continue

            parts = cmd.split(maxsplit=1)
            action = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if action == "q":
                print("再见!")
                break
            elif action == "s" and arg:
                do_search(storage, arg, "semantic")
            elif action == "k" and arg:
                do_search(storage, arg, "keyword")
            elif action == "l":
                limit = int(arg) if arg.isdigit() else 20
                show_list(storage, limit)
            elif action == "d" and arg:
                show_detail(storage, arg)
            elif action == "o":
                show_overview(storage)
            else:
                print("未知命令。输入 q 退出。")

        except KeyboardInterrupt:
            print("\n再见!")
            break
        except Exception as e:
            print(f"错误: {e}")


def main():
    parser = argparse.ArgumentParser(description="文献数据库查看工具")
    parser.add_argument(
        "--storage-dir",
        type=str,
        default="data/literature",
        help="文献存储目录"
    )
    parser.add_argument(
        "--search",
        type=str,
        help="语义搜索"
    )
    parser.add_argument(
        "--keyword",
        type=str,
        help="关键词搜索"
    )
    parser.add_argument(
        "--list",
        type=int,
        nargs="?",
        const=20,
        help="列出最近的文献"
    )
    parser.add_argument(
        "--detail",
        type=str,
        help="查看文献详情 (传入ID)"
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="进入交互模式"
    )

    args = parser.parse_args()

    # 初始化存储
    storage = LiteratureStorageTool(storage_dir=args.storage_dir)

    # 执行操作
    if args.search:
        do_search(storage, args.search, "semantic")
    elif args.keyword:
        do_search(storage, args.keyword, "keyword")
    elif args.list:
        show_list(storage, args.list)
    elif args.detail:
        show_detail(storage, args.detail)
    elif args.interactive:
        interactive_mode(storage)
    else:
        # 默认显示概览
        show_overview(storage)


if __name__ == "__main__":
    main()
