#!/usr/bin/env python3
"""
文献搜集器使用本地数据库的示例

演示如何:
1. 导入文献到本地数据库
2. 使用 LiteratureCollectorAgent 自动检索本地数据库
3. Agent 会优先使用本地数据库，不足时才补充
"""

from pathlib import Path
from loguru import logger

from agents import LiteratureCollectorAgent
from tools.literature_storage import get_literature_storage

# 配置日志
logger.remove()
logger.add(
    lambda msg: print(msg, end=""),
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    level="INFO"
)


def prepare_sample_literature(storage_dir: str = "data/literature"):
    """
    准备示例文献数据

    Args:
        storage_dir: 存储目录
    """
    logger.info("=" * 70)
    logger.info("步骤1: 准备示例文献数据")
    logger.info("=" * 70)

    # 获取文献存储工具
    lit_storage = get_literature_storage(storage_dir)

    # 检查现有文献
    stats = lit_storage.get_statistics()
    logger.info(f"当前数据库状态: {stats['total_count']} 篇文献")

    # 如果数据库为空，添加一些示例文献
    if stats['total_count'] == 0:
        logger.info("数据库为空，添加示例文献...")

        sample_papers = [
            {
                "authors": "Porter, M. E. & van der Linde, C.",
                "year": 1995,
                "title": "Toward a New Conception of the Environment-Competitiveness Relationship",
                "journal": "Journal of Economic Perspectives",
                "variable_x_definition": "环境监管严格程度",
                "variable_x_measurement": "污染排放标准、环保法律数量",
                "variable_y_definition": "企业竞争力",
                "variable_y_measurement": "全要素生产率、创新产出",
                "core_conclusion": "严格的环境监管能够促进企业创新，提升长期竞争力（波特假说）",
                "theoretical_mechanism": ["创新补偿机制", "先行者优势", "管理效率提升"],
                "identification_strategy": "跨国面板数据回归",
                "data_source": "OECD工业数据库",
                "heterogeneity_dimensions": ["行业技术密集度", "企业规模"],
                "limitations": ["缺乏微观企业层面数据", "内生性问题未充分解决"]
            },
            {
                "authors": "李春涛 & 宋敏",
                "year": 2010,
                "title": "中国制造业企业的污染排放与环境管制",
                "journal": "经济研究",
                "variable_x_definition": "环境规制强度",
                "variable_x_measurement": "排污费征收、环保投资占比",
                "variable_y_definition": "企业全要素生产率",
                "variable_y_measurement": "LP方法估计的TFP",
                "core_conclusion": "环境规制对企业TFP存在显著负向影响，但在高技术行业影响较小",
                "theoretical_mechanism": ["成本上升效应", "资源挤出效应"],
                "identification_strategy": "固定效应模型、工具变量法",
                "data_source": "工业企业数据库、环境统计年鉴",
                "heterogeneity_dimensions": ["所有制类型", "技术密集度", "区域"],
                "limitations": ["短期效应为主", "缺乏长期追踪"]
            },
            {
                "authors": "Greenstone, M.",
                "year": 2002,
                "title": "The Impacts of Environmental Regulations on Industrial Activity",
                "journal": "Journal of Political Economy",
                "variable_x_definition": "空气质量法案实施",
                "variable_x_measurement": "非达标地区虚拟变量",
                "variable_y_definition": "制造业就业和产出",
                "variable_y_measurement": "县级制造业就业人数、总产值",
                "core_conclusion": "环境规制导致污染密集型产业就业下降约15%",
                "theoretical_mechanism": ["生产成本上升", "产业转移"],
                "identification_strategy": "倍差法（DID）",
                "data_source": "美国县级经济普查数据",
                "heterogeneity_dimensions": ["产业污染密集度"],
                "limitations": ["仅考察短期效应", "未考察生产率变化"]
            }
        ]

        for paper in sample_papers:
            lit_storage.add_literature(paper, source="sample_data")

        logger.info(f"已添加 {len(sample_papers)} 篇示例文献")

    # 显示最终统计
    stats = lit_storage.get_statistics()
    logger.info(f"最终数据库状态: {stats['total_count']} 篇文献")
    logger.info("")

    return lit_storage


def test_literature_collector_with_db():
    """测试使用本地数据库的文献搜集器"""
    logger.info("=" * 70)
    logger.info("步骤2: 运行 LiteratureCollectorAgent（会自动检索本地数据库）")
    logger.info("=" * 70)

    # 初始化 Agent
    agent = LiteratureCollectorAgent(
        literature_storage_dir="data/literature"
    )

    # 运行任务
    result = agent.run({
        "research_topic": "环境监管对企业全要素生产率的影响",
        "keyword_group_a": ["环境监管", "环境规制", "污染排放"],
        "keyword_group_b": ["全要素生产率", "TFP", "企业绩效"],
        "min_papers": 5
    })

    # 显示结果
    logger.info("=" * 70)
    logger.info("步骤3: 显示结果")
    logger.info("=" * 70)

    # 工具调用情况
    tool_calls = result.get("tool_calls", [])
    if tool_calls:
        logger.info(f"Agent 调用了 {len(tool_calls)} 次工具:")
        for i, call in enumerate(tool_calls, 1):
            logger.info(f"  {i}. {call['tool']}: {call['args']}")
    else:
        logger.warning("Agent 未调用任何工具（可能本地数据库不可用）")

    logger.info("")

    # 文献列表
    literature_list = result.get("literature_list", [])
    logger.info(f"收集到 {len(literature_list)} 篇文献:")
    for lit in literature_list[:5]:  # 只显示前5篇
        logger.info(f"  - {lit.get('authors', 'N/A')} ({lit.get('year', 'N/A')}). {lit.get('title', 'N/A')}")
        logger.info(f"    期刊: {lit.get('journal', 'N/A')}")

    logger.info("=" * 70)
    logger.info("完成！")
    logger.info("=" * 70)

    return result


def main():
    """主函数"""
    # 1. 准备示例文献数据
    lit_storage = prepare_sample_literature()

    # 2. 测试文献搜集器
    result = test_literature_collector_with_db()

    logger.info("\n提示:")
    logger.info("  - 你可以使用 tools/literature_storage.py 中的工具手动导入更多文献")
    logger.info("  - 支持从 CSV、JSON 导入，或使用 import_from_literature_collector() 保存之前的搜集结果")
    logger.info("  - 下次运行 LiteratureCollectorAgent 时，它会自动检索本地数据库")


if __name__ == "__main__":
    main()
