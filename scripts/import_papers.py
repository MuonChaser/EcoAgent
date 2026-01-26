"""
导入实证论文数据到文献数据库

使用方法:
    python scripts/import_papers.py
    python scripts/import_papers.py --csv data/raw/实证论文提取结果.csv
"""
import argparse
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.literature_storage import LiteratureStorageTool
from loguru import logger


def main():
    parser = argparse.ArgumentParser(description="导入实证论文数据到文献数据库")
    parser.add_argument(
        "--csv",
        type=str,
        default="data/raw/实证论文提取结果.csv",
        help="CSV文件路径"
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
        help="批量导入大小"
    )

    args = parser.parse_args()

    # 检查文件是否存在
    csv_path = Path(args.csv)
    if not csv_path.exists():
        logger.error(f"CSV文件不存在: {csv_path}")
        sys.exit(1)

    logger.info(f"开始导入实证论文数据")
    logger.info(f"CSV文件: {csv_path}")
    logger.info(f"存储目录: {args.storage_dir}")

    # 初始化存储工具
    storage = LiteratureStorageTool(storage_dir=args.storage_dir)

    # 执行导入
    result = storage.import_from_csv(
        csv_path=str(csv_path),
        research_project=args.project,
        batch_size=args.batch_size
    )

    # 显示结果
    print("\n" + "=" * 60)
    print("导入完成!")
    print("=" * 60)
    print(f"总行数: {result.get('total', 0)}")
    print(f"成功导入: {result.get('imported', 0)}")
    print(f"跳过: {result.get('skipped', 0)}")
    print(f"错误: {result.get('errors', 0)}")

    # 显示数据库统计
    stats = storage.get_statistics()
    print(f"\n数据库当前状态:")
    print(f"  总文献数: {stats.get('total_count', 0)}")
    print(f"  存储路径: {stats.get('storage_path', 'N/A')}")
    print(f"  向量数据库: {'已启用' if stats.get('chroma_available') else '未启用'}")


if __name__ == "__main__":
    main()
