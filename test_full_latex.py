"""
完整测试 LaTeX 论文生成流程
"""

from agents.report_writer import ReportWriterAgent
from tools.output_tools import ReportGenerator
from loguru import logger

def test_full_latex_workflow():
    """测试完整的 LaTeX 工作流"""
    logger.info("="*70)
    logger.info("测试完整 LaTeX 生成工作流")
    logger.info("="*70)

    # 1. 创建 ReportWriter agent
    agent = ReportWriterAgent()

    # 2. 准备输入数据
    input_data = {
        "research_topic": "数字化转型对企业创新的影响研究",
        "literature_summary": "现有研究表明数字化转型显著提升企业创新能力，但因果机制尚不清晰...",
        "variable_system": "X: 数字化投入强度（IT资本占总资产比重）; Y: 创新绩效（发明专利数对数）",
        "theory_framework": "基于TOE（技术-组织-环境）框架和内生增长理论",
        "model_design": "双向固定效应模型，控制企业和年份固定效应",
        "data_analysis": "基准回归系数为0.218***，数字化投入每提升1个标准差，专利数增加35.2%",
        "word_count": 5000
    }

    # 3. 运行 agent 生成报告
    logger.info("\n步骤 1/3: 运行 ReportWriter Agent...")
    result = agent.run(input_data)
    logger.info(f"✅ Agent 运行完成")

    # 4. 使用 ReportGenerator 保存为 LaTeX
    logger.info("\n步骤 2/3: 使用 ReportGenerator 保存 LaTeX 论文...")
    output_tools = ReportGenerator(output_dir="output/research")

    latex_path = output_tools.generate_full_report(
        research_topic="数字化转型对企业创新的影响研究",
        results=result,
        format="latex"
    )

    logger.info(f"\n步骤 3/3: 检查生成的文件...")
    if latex_path:
        logger.info(f"✅ LaTeX 论文已保存: {latex_path}")

        # 读取文件验证
        with open(latex_path, "r", encoding="utf-8") as f:
            content = f.read()

        if "\\documentclass" in content and "\\end{document}" in content:
            logger.info(f"✅ LaTeX 文件格式正确")
            logger.info(f"✅ 文件大小: {len(content)} 字符")

            # 显示前几行
            lines = content.split("\n")[:15]
            logger.info(f"\n前 15 行:")
            for i, line in enumerate(lines, 1):
                logger.info(f"  {i:3d}: {line}")

            return True
        else:
            logger.error("❌ LaTeX 文件格式不完整")
            return False
    else:
        logger.error("❌ 未能生成 LaTeX 文件")
        return False

if __name__ == "__main__":
    logger.info("\n" + "="*70)
    logger.info("开始完整 LaTeX 测试")
    logger.info("="*70 + "\n")

    success = test_full_latex_workflow()

    logger.info("\n" + "="*70)
    if success:
        logger.info("✅✅✅ 测试成功！LaTeX 生成功能正常工作！")
    else:
        logger.error("❌❌❌ 测试失败")
    logger.info("="*70)
