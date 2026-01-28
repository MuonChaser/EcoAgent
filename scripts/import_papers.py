"""
导入实证论文数据到文献数据库

使用方法:
    # 从CSV导入
    python scripts/import_papers.py
    python scripts/import_papers.py --csv data/raw/实证论文提取结果.csv

    # 从PDF目录导入（自动从文件名提取作者和年份）
    python scripts/import_papers.py --pdf-dir "data/raw/环境监管对企业全要素生产率的影响"

    # 提取PDF文本内容作为摘要
    python scripts/import_papers.py --pdf-dir "data/raw/论文目录" --extract-text
"""
import argparse
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.literature_storage import LiteratureStorageTool
from loguru import logger


def import_csv(storage, csv_path, project, batch_size):
    """从CSV导入"""
    result = storage.import_from_csv(
        csv_path=str(csv_path),
        research_project=project,
        batch_size=batch_size
    )

    print("\n" + "=" * 60)
    print("CSV导入完成!")
    print("=" * 60)
    print(f"总行数: {result.get('total', 0)}")
    print(f"成功导入: {result.get('imported', 0)}")
    print(f"跳过: {result.get('skipped', 0)}")
    print(f"错误: {result.get('errors', 0)}")

    return result


def import_pdf_dir(storage, pdf_dir, project, extract_text):
    """从PDF目录导入"""
    result = storage.import_from_pdf_directory(
        pdf_dir=str(pdf_dir),
        research_project=project,
        extract_text=extract_text
    )

    print("\n" + "=" * 60)
    print("PDF目录导入完成!")
    print("=" * 60)
    print(f"总PDF数: {result.get('total', 0)}")
    print(f"成功导入: {result.get('imported', 0)}")
    print(f"错误: {result.get('errors', 0)}")

    if result.get('imported_ids'):
        print(f"\n导入的文献:")
        for item_id in result['imported_ids'][:10]:
            item = storage.get_literature(item_id)
            if item:
                print(f"  [{item_id}] {item.title}")
                print(f"          作者: {item.authors}, 年份: {item.year}")
        if len(result['imported_ids']) > 10:
            print(f"  ... 还有 {len(result['imported_ids']) - 10} 篇")

    return result


def main():
    parser = argparse.ArgumentParser(description="导入实证论文数据到文献数据库")
    parser.add_argument(
        "--csv",
        type=str,
        help="CSV文件路径"
    )
    parser.add_argument(
        "--pdf-dir",
        type=str,
        help="PDF文件目录路径（自动从文件名提取作者和年份）"
    )
    parser.add_argument(
        "--extract-text",
        action="store_true",
        help="提取PDF文本内容作为摘要（需要PyPDF2）"
    )
    parser.add_argument(
        "--storage-dir",
        type=str,
        default="data/literature",
        help="文献存储目录"
    )
    parser.add_argument(
        "--project",
        type=str,
        default="实证论文库",
        help="关联的研究项目名称"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="批量导入大小（CSV导入时使用）"
    )

    args = parser.parse_args()

    # 初始化存储工具
    storage = LiteratureStorageTool(storage_dir=args.storage_dir)
    logger.info(f"存储目录: {args.storage_dir}")

    # 根据参数执行不同的导入
    if args.pdf_dir:
        # PDF目录导入
        pdf_path = Path(args.pdf_dir)
        if not pdf_path.exists():
            logger.error(f"PDF目录不存在: {pdf_path}")
            sys.exit(1)
        logger.info(f"开始从PDF目录导入: {pdf_path}")
        import_pdf_dir(storage, pdf_path, args.project, args.extract_text)

    elif args.csv:
        # CSV文件导入
        csv_path = Path(args.csv)
        if not csv_path.exists():
            logger.error(f"CSV文件不存在: {csv_path}")
            sys.exit(1)
        logger.info(f"开始从CSV导入: {csv_path}")
        import_csv(storage, csv_path, args.project, args.batch_size)

    else:
        # 默认：CSV导入
        csv_path = Path("data/raw/实证论文提取结果.csv")
        if csv_path.exists():
            logger.info(f"开始从默认CSV导入: {csv_path}")
            import_csv(storage, csv_path, args.project, args.batch_size)
        else:
            print("使用方法:")
            print("  从CSV导入: python scripts/import_papers.py --csv <csv文件路径>")
            print("  从PDF导入: python scripts/import_papers.py --pdf-dir <pdf目录路径>")
            sys.exit(0)

    # 显示数据库统计
    stats = storage.get_statistics()
    print(f"\n数据库当前状态:")
    print(f"  总文献数: {stats.get('total_count', 0)}")
    print(f"  存储路径: {stats.get('storage_path', 'N/A')}")
    print(f"  向量数据库: {'已启用' if stats.get('chroma_available') else '未启用'}")


if __name__ == "__main__":
    main()
