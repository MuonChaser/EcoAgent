#!/usr/bin/env python3
"""
数据工具使用示例

本示例展示如何:
1. 导入数据到RAG库
2. 搜索合适的数据集
3. 预览和分析数据
4. 使用DataAnalystAgent（已集成数据工具）

使用前请确保:
1. 已安装依赖: pip install pandas chromadb sentence-transformers
2. data/raw 目录中有数据文件
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger

# 配置日志
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO"
)


def example_1_import_data():
    """示例1: 导入数据到RAG库"""
    print("\n" + "=" * 60)
    print("示例1: 导入数据到RAG库")
    print("=" * 60)

    from tools.data_storage import get_data_storage
    from config.config import RAW_DATA_DIR

    # 初始化数据存储
    storage = get_data_storage()

    # 扫描并导入 data/raw 目录
    print(f"\n扫描目录: {RAW_DATA_DIR}")
    stats = storage.scan_directory(
        directory=str(RAW_DATA_DIR),
        patterns=["*.csv", "*.xlsx"],
        auto_extract=True
    )

    print(f"\n导入结果:")
    print(f"  总文件数: {stats['total_files']}")
    print(f"  成功导入: {stats['imported']}")
    print(f"  跳过: {stats['skipped']}")

    # 查看统计信息
    db_stats = storage.get_statistics()
    print(f"\n数据库统计:")
    print(f"  总数据集: {db_stats['total_count']}")
    print(f"  按类型: {db_stats['by_type']}")

    return storage


def example_2_search_datasets(storage=None):
    """示例2: 搜索数据集"""
    print("\n" + "=" * 60)
    print("示例2: 搜索数据集")
    print("=" * 60)

    if storage is None:
        from tools.data_storage import get_data_storage
        storage = get_data_storage()

    # 语义搜索
    print("\n1. 语义搜索: '企业创新研发投入'")
    results = storage.search_semantic("企业创新研发投入", n_results=3)
    for item in results.items:
        print(f"   [{item.id}] {item.name}")
        print(f"       描述: {item.description[:80]}...")

    # 关键词搜索
    print("\n2. 关键词搜索: 'DID'")
    results = storage.search_keyword("DID", n_results=3)
    for item in results.items:
        print(f"   [{item.id}] {item.name}")

    # 混合搜索
    print("\n3. 混合搜索: '面板数据'")
    results = storage.search_hybrid("面板数据", n_results=3)
    for item in results.items:
        print(f"   [{item.id}] {item.name}")

    return results


def example_3_preview_data():
    """示例3: 预览数据"""
    print("\n" + "=" * 60)
    print("示例3: 预览数据")
    print("=" * 60)

    from tools.data_tools import get_data_tools

    # 初始化数据工具
    tools = get_data_tools()

    # 查找数据文件
    data_file = project_root / "data" / "raw" / "实证论文提取结果.csv"
    if not data_file.exists():
        print(f"数据文件不存在: {data_file}")
        return None

    # 预览数据
    print(f"\n预览文件: {data_file.name}")
    preview = tools.preview_data(str(data_file), n_rows=5)

    print(f"\n数据概况:")
    print(f"  总行数: {preview.total_rows}")
    print(f"  总列数: {preview.total_columns}")
    print(f"  列名: {preview.columns}")
    print(f"  内存使用: {preview.memory_usage}")

    print(f"\n前5行数据:")
    for i, row in enumerate(preview.head[:5]):
        print(f"  {i+1}. {list(row.values())[:3]}...")

    return preview


def example_4_data_statistics():
    """示例4: 获取数据统计"""
    print("\n" + "=" * 60)
    print("示例4: 获取数据统计")
    print("=" * 60)

    from tools.data_tools import get_data_tools

    tools = get_data_tools()

    data_file = project_root / "data" / "raw" / "实证论文提取结果.csv"
    if not data_file.exists():
        print(f"数据文件不存在: {data_file}")
        return None

    # 获取统计信息
    print(f"\n分析文件: {data_file.name}")
    stats = tools.get_statistics(str(data_file))

    print(f"\n缺失值统计:")
    for col, missing in list(stats.missing_stats.items())[:5]:
        print(f"  {col}: {missing['missing_count']} ({missing['missing_ratio']*100:.1f}%)")

    print(f"\n分类变量统计:")
    for col, cat_stats in list(stats.categorical_stats.items())[:3]:
        print(f"  {col}:")
        print(f"    唯一值数: {cat_stats['unique_count']}")
        print(f"    最常见: {cat_stats['most_common']}")

    return stats


def example_5_query_data():
    """示例5: 查询数据"""
    print("\n" + "=" * 60)
    print("示例5: 查询数据")
    print("=" * 60)

    from tools.data_tools import get_data_tools

    tools = get_data_tools()

    data_file = project_root / "data" / "raw" / "实证论文提取结果.csv"
    if not data_file.exists():
        print(f"数据文件不存在: {data_file}")
        return None

    # 查询特定条件的数据
    print(f"\n查询包含'DID'方法的论文:")
    try:
        result = tools.query_data(
            str(data_file),
            columns=["文章名称", "计量模型 (方法)"],
            limit=10
        )

        print(f"  找到 {result.total_matched} 条记录")
        for row in result.data[:5]:
            print(f"  - {row.get('文章名称', 'N/A')[:50]}...")
    except Exception as e:
        print(f"  查询出错: {e}")

    return result


def example_6_data_analyst_agent():
    """示例6: 使用数据分析Agent"""
    print("\n" + "=" * 60)
    print("示例6: 使用数据分析Agent (集成数据工具)")
    print("=" * 60)

    from agents import DataAnalystAgent

    # 初始化Agent
    print("\n初始化 DataAnalystAgent...")
    agent = DataAnalystAgent()

    # 搜索相关数据
    print("\n1. 搜索相关数据集:")
    datasets = agent.search_data("实证研究方法", n_results=3)
    for d in datasets:
        print(f"   - {d['name']}: {d.get('row_count', 'N/A')}行")

    # 如果有数据文件，进行分析
    data_file = project_root / "data" / "raw" / "实证论文提取结果.csv"
    if data_file.exists():
        print(f"\n2. 预览数据集:")
        preview = agent.preview_dataset(str(data_file), n_rows=5)
        print(f"   行数: {preview['total_rows']}")
        print(f"   列数: {preview['total_columns']}")
        print(f"   列名: {preview['columns'][:5]}...")

        print(f"\n3. 获取统计信息:")
        stats = agent.get_data_statistics(str(data_file))
        print(f"   缺失值列数: {len(stats['missing_stats'])}")

    return agent


def example_7_langchain_tools():
    """示例7: 使用LangChain工具"""
    print("\n" + "=" * 60)
    print("示例7: 使用LangChain工具")
    print("=" * 60)

    from tools.data_tools import get_langchain_data_tools

    # 获取LangChain格式的工具
    tools = get_langchain_data_tools()

    print(f"\n可用的LangChain工具:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:60]}...")

    # 调用工具示例
    print(f"\n调用 search_datasets 工具:")
    search_tool = tools[0]  # search_datasets
    result = search_tool.invoke({"query": "面板数据", "n_results": 2})
    print(f"  结果: {result[:200]}...")

    return tools


def main():
    """运行所有示例"""
    print("\n🚀 数据工具使用示例")
    print("=" * 60)

    try:
        # 示例1: 导入数据
        storage = example_1_import_data()

        # 示例2: 搜索数据集
        example_2_search_datasets(storage)

        # 示例3: 预览数据
        example_3_preview_data()

        # 示例4: 数据统计
        example_4_data_statistics()

        # 示例5: 查询数据
        example_5_query_data()

        # 示例6: 数据分析Agent (需要API配置)
        try:
            example_6_data_analyst_agent()
        except Exception as e:
            print(f"\nDataAnalystAgent示例跳过 (可能缺少API配置): {e}")

        # 示例7: LangChain工具
        example_7_langchain_tools()

        print("\n" + "=" * 60)
        print("✅ 所有示例运行完成!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 示例运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
