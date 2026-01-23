"""
测试 LaTeX 输出功能

该脚本演示如何使用 ReportWriterAgent 生成符合经济学规范的 LaTeX 论文
"""

from orchestrator import ResearchOrchestrator
from loguru import logger

def test_latex_output():
    """测试生成 LaTeX 格式论文"""

    logger.info("=" * 70)
    logger.info("测试 LaTeX 论文生成功能")
    logger.info("=" * 70)

    # 创建编排器
    orchestrator = ResearchOrchestrator(output_dir="output/research")

    # 运行完整研究流程（使用自然语言输入）
    results = orchestrator.run_full_pipeline(
        user_input="我想研究数字化转型对企业创新绩效的影响",
        enable_steps=["input_parse", "literature", "variable", "theory", "model", "analysis", "report"],
        min_papers=8,
        word_count=12000,  # 论文字数要求
    )

    logger.info("\n" + "=" * 70)
    logger.info("生成结果:")
    logger.info("=" * 70)
    logger.info(f"LaTeX论文: {results.get('latex_path', 'N/A')}")
    logger.info(f"Markdown备份: {results.get('report_path', 'N/A')}")
    logger.info(f"JSON数据: {results.get('json_path', 'N/A')}")
    logger.info("=" * 70)

    return results


def test_traditional_input():
    """测试传统输入方式（指定关键词）"""

    logger.info("=" * 70)
    logger.info("测试传统输入方式")
    logger.info("=" * 70)

    orchestrator = ResearchOrchestrator(output_dir="output/research")

    results = orchestrator.run_full_pipeline(
        research_topic="碳交易政策对企业绿色创新的影响研究",
        keyword_group_a=["碳交易", "碳市场", "Carbon Trading"],
        keyword_group_b=["绿色创新", "环境创新", "Green Innovation"],
        min_papers=10,
        word_count=15000,
    )

    logger.info("\n" + "=" * 70)
    logger.info("生成结果:")
    logger.info("=" * 70)
    logger.info(f"LaTeX论文: {results.get('latex_path', 'N/A')}")
    logger.info("=" * 70)

    return results


def test_single_report_step():
    """测试单独运行 ReportWriter 步骤"""

    logger.info("=" * 70)
    logger.info("测试单独运行 ReportWriter")
    logger.info("=" * 70)

    orchestrator = ResearchOrchestrator(output_dir="output/research")

    # 模拟前置步骤的输出
    input_data = {
        "research_topic": "人工智能对劳动力市场的影响",
        "literature_summary": "现有文献表明AI技术对劳动力市场产生了显著影响...",
        "variable_system": "核心解释变量：AI采纳强度；被解释变量：就业率...",
        "theory_framework": "基于技术偏向型进步理论...",
        "model_design": "采用双向固定效应模型...",
        "data_analysis": "基准回归结果显示...",
        "word_count": 10000,
    }

    result = orchestrator.run_single_step(
        step="report",
        input_data=input_data
    )

    logger.info(f"\n生成的报告长度: {len(result.get('final_report', ''))} 字符")
    logger.info(f"是否包含 LaTeX 代码: {'\\documentclass' in result.get('final_report', '')}")

    return result


if __name__ == "__main__":
    import sys

    # 根据命令行参数选择测试模式
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"

    if mode == "full":
        logger.info("运行完整流程测试（自然语言输入）")
        test_latex_output()
    elif mode == "traditional":
        logger.info("运行完整流程测试（传统关键词输入）")
        test_traditional_input()
    elif mode == "single":
        logger.info("运行单步骤测试（仅 ReportWriter）")
        test_single_report_step()
    else:
        logger.error(f"未知的测试模式: {mode}")
        logger.info("可用模式: full, traditional, single")
        sys.exit(1)
