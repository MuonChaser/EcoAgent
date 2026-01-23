#!/usr/bin/env python
"""
完整研究流程 - 从自然语言输入到完整报告
使用方式: python run_research.py
"""
from orchestrator import ResearchOrchestrator
from loguru import logger
import sys


def main():
    """运行完整的研究流程"""
    
    # 用户输入
    user_input = "我想研究数字化转型对企业创新绩效的影响"
    
    logger.info("=" * 80)
    logger.info("🚀 开始经济学研究：AI for Econometrics")
    logger.info("=" * 80)
    logger.info(f"\n📝 研究问题: {user_input}\n")
    
    # 初始化编排器
    orchestrator = ResearchOrchestrator(output_dir="output/research")
    
    try:
        # 运行完整流程
        logger.info("🔄 启动多智能体研究流程...\n")
        
        result = orchestrator.run_full_pipeline(
            user_input=user_input,
            enable_steps=[
                "input_parse",    # 0. 输入解析
                "literature",     # 1. 文献搜集
                "variable",       # 2. 指标设置
                "theory",         # 3. 理论设置
                "model",          # 4. 模型设计
                # "analysis",     # 5. 数据分析（需要真实数据）
                # "report",       # 6. 报告撰写
            ],
            min_papers=8,         # 搜集至少8篇文献
            enable_review=False,  # 暂不启用审稿
        )
        
        # 输出结果摘要
        logger.info("\n" + "=" * 80)
        logger.info("✅ 研究流程完成！")
        logger.info("=" * 80)
        
        logger.info(f"\n📊 研究主题: {result.get('research_topic')}")
        
        if "input_parsed_data" in result:
            parsed = result["input_parsed_data"]
            logger.info(f"\n🔍 核心变量:")
            logger.info(f"  • 解释变量(X): {parsed.get('variable_x', {}).get('chinese')}")
            logger.info(f"  • 被解释变量(Y): {parsed.get('variable_y', {}).get('chinese')}")
        
        if "literature_list" in result:
            lit_count = len(result["literature_list"])
            logger.info(f"\n📚 文献搜集: {lit_count} 篇核心文献")
            
            if lit_count > 0:
                logger.info("\n前3篇文献示例:")
                for i, lit in enumerate(result["literature_list"][:3], 1):
                    logger.info(f"  {i}. {lit.get('title', 'N/A')}")
                    logger.info(f"     作者: {lit.get('authors', 'N/A')} ({lit.get('year', 'N/A')})")
                    logger.info(f"     期刊: {lit.get('journal', 'N/A')}\n")
        
        if "variable_system_data" in result:
            var_data = result["variable_system_data"]
            logger.info("📐 变量体系设计完成:")
            
            core_vars = var_data.get("core_variables", {})
            x_vars = core_vars.get("explanatory_variable_x", [])
            y_vars = core_vars.get("dependent_variable_y", [])
            control_vars = var_data.get("control_variables", [])
            
            logger.info(f"  • 解释变量: {len(x_vars)} 个")
            logger.info(f"  • 被解释变量: {len(y_vars)} 个")
            logger.info(f"  • 控制变量: {len(control_vars)} 个")
        
        if "theory_framework_data" in result:
            theory_data = result["theory_framework_data"]
            theories = theory_data.get("theoretical_framework", [])
            hypotheses = theory_data.get("research_hypotheses", [])
            
            logger.info(f"\n📖 理论框架:")
            logger.info(f"  • 理论基础: {len(theories)} 个理论")
            logger.info(f"  • 研究假设: {len(hypotheses)} 个假设")
            
            if hypotheses:
                logger.info("\n假设示例:")
                for i, hyp in enumerate(hypotheses[:2], 1):
                    logger.info(f"  H{i}: {hyp.get('hypothesis_content', 'N/A')}")
        
        if "model_design_data" in result:
            model_data = result["model_design_data"]
            logger.info(f"\n🧮 计量模型:")
            
            baseline = model_data.get("baseline_model", {})
            logger.info(f"  • 基准模型: {baseline.get('model_type', 'N/A')}")
            
            mechanism = model_data.get("mechanism_models", [])
            heterogeneity = model_data.get("heterogeneity_models", [])
            robustness = model_data.get("robustness_checks", [])
            
            logger.info(f"  • 机制检验: {len(mechanism)} 个模型")
            logger.info(f"  • 异质性分析: {len(heterogeneity)} 个维度")
            logger.info(f"  • 稳健性检验: {len(robustness)} 个方法")
        
        # 输出文件位置
        logger.info("\n" + "=" * 80)
        logger.info("📁 输出文件:")
        logger.info("=" * 80)
        logger.info("  • 完整报告: output/research/report_*.md")
        logger.info("  • JSON数据: output/research/report_*.json")
        logger.info("  • 阶段结果: output/research/stages/*.json")
        
        logger.success("\n✨ 研究流程成功完成！")
        
        return result
        
    except Exception as e:
        logger.error(f"\n❌ 研究流程出错: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
