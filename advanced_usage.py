"""
高级使用示例 - 包含输入解析和审稿人功能
"""
from main import ResearchOrchestrator
from loguru import logger


def example_with_input_parser():
    """
    示例：使用输入解析功能
    """
    orchestrator = ResearchOrchestrator(output_dir="output")
    
    # 用户的自然语言输入
    user_input = "我想研究绿色债券对企业业绩的影响"
    
    # 运行完整流程，从输入解析开始
    results = orchestrator.run_full_pipeline(
        user_input=user_input,
        enable_steps=["input_parse", "literature", "variable", "theory", "model", "analysis", "report"],
        min_papers=10,
        word_count=8000,
    )
    
    print("\n" + "=" * 50)
    print("研究流程完成！")
    print("=" * 50)
    print(f"用户输入: {user_input}")
    print(f"研究主题: {results['research_topic']}")
    if "parsed_input" in results:
        print(f"\n解析结果:\n{results['parsed_input'][:500]}...")
    print(f"\n报告路径: {results.get('report_path', 'N/A')}")
    print("=" * 50)
    
    return results


def example_with_reviewer():
    """
    示例：运行完整流程并进行审稿
    """
    orchestrator = ResearchOrchestrator(output_dir="output")
    
    # 运行完整流程，包括审稿
    results = orchestrator.run_full_pipeline(
        research_topic="数字化转型对企业创新的影响研究",
        keyword_group_a=["数字化转型", "Digital Transformation", "数字技术"],
        keyword_group_b=["企业创新", "Innovation", "技术创新"],
        min_papers=10,
        word_count=8000,
        enable_review=True,  # 启用审稿功能
    )
    
    print("\n" + "=" * 50)
    print("研究流程完成（含审稿）！")
    print("=" * 50)
    print(f"研究主题: {results['research_topic']}")
    print(f"报告路径: {results.get('report_path', 'N/A')}")
    if "review_report" in results:
        print(f"\n审稿意见预览:\n{results['review_report'][:500]}...")
    print("=" * 50)
    
    return results


def example_parse_and_review():
    """
    示例：完整流程 - 从输入解析到审稿
    """
    orchestrator = ResearchOrchestrator(output_dir="output")
    
    # 用户的自然语言输入
    user_input = "我想研究碳交易政策对企业绿色创新的影响，特别是上市公司的表现"
    
    # 运行完整流程
    results = orchestrator.run_full_pipeline(
        user_input=user_input,
        enable_steps=[
            "input_parse",   # 解析输入
            "literature",    # 文献搜集
            "variable",      # 变量设计
            "theory",        # 理论构建
            "model",         # 模型设计
            "analysis",      # 数据分析
            "report",        # 报告撰写
            "review",        # 审稿评审
        ],
        min_papers=12,
        word_count=10000,
    )
    
    print("\n" + "=" * 70)
    print("完整研究流程完成（输入解析 + 研究 + 审稿）！")
    print("=" * 70)
    print(f"原始输入: {user_input}")
    print(f"研究主题: {results['research_topic']}")
    print(f"\n报告路径: {results.get('report_path', 'N/A')}")
    print(f"JSON路径: {results.get('json_path', 'N/A')}")
    
    if "parsed_input" in results:
        print(f"\n【输入解析摘要】")
        print(results['parsed_input'][:300] + "...")
    
    if "review_report" in results:
        print(f"\n【审稿意见摘要】")
        print(results['review_report'][:300] + "...")
    
    print("=" * 70)
    
    return results


def example_single_step_parse():
    """
    示例：单独运行输入解析
    """
    orchestrator = ResearchOrchestrator(output_dir="output")
    
    # 只运行输入解析
    result = orchestrator.run_single_step(
        step="input_parse",
        input_data={
            "user_input": "我想研究人工智能技术对劳动力市场的影响，特别关注就业结构的变化",
        }
    )
    
    print("\n输入解析完成！")
    print("=" * 50)
    print(result.get("parsed_input", ""))
    print("=" * 50)
    
    return result


def example_single_step_review():
    """
    示例：单独运行审稿评审
    """
    orchestrator = ResearchOrchestrator(output_dir="output")
    
    # 假设已经有了研究成果
    result = orchestrator.run_single_step(
        step="review",
        input_data={
            "research_topic": "区块链技术对供应链金融的影响研究",
            "variable_system": "（这里是变量体系内容）",
            "theory_framework": "（这里是理论框架内容）",
            "model_design": "（这里是模型设计内容）",
            "data_analysis": "（这里是数据分析内容）",
            "final_report": "（这里是完整报告内容）",
        }
    )
    
    print("\n审稿评审完成！")
    print("=" * 50)
    print(result.get("review_report", "")[:500] + "...")
    print("=" * 50)
    
    return result


def example_iterative_improvement():
    """
    示例：迭代改进 - 研究、审稿、修改
    """
    orchestrator = ResearchOrchestrator(output_dir="output")
    
    # 第一轮：完整研究
    print("\n【第一轮：初始研究】")
    results_round1 = orchestrator.run_full_pipeline(
        research_topic="平台经济对中小企业发展的影响",
        keyword_group_a=["平台经济", "Platform Economy", "数字平台"],
        keyword_group_b=["中小企业", "SME", "企业发展"],
        min_papers=10,
        word_count=8000,
        enable_review=True,  # 第一轮就进行审稿
    )
    
    print("\n第一轮研究完成！")
    print(f"报告路径: {results_round1.get('report_path')}")
    
    if "review_report" in results_round1:
        print("\n审稿意见已生成，可根据意见进行修改...")
        print(results_round1['review_report'][:300] + "...")
    
    # 实际应用中，可以根据审稿意见重新运行某些步骤
    # 例如：重新设计变量、调整模型等
    
    return results_round1


if __name__ == "__main__":
    print("=" * 70)
    print("AI for Econometrics 多智能体系统 - 高级功能示例")
    print("=" * 70)
    
    print("\n请选择要运行的示例：")
    print("1. 使用输入解析功能")
    print("2. 运行完整流程并审稿")
    print("3. 完整流程（解析+研究+审稿）")
    print("4. 单独运行输入解析")
    print("5. 单独运行审稿评审")
    print("6. 迭代改进示例")
    
    choice = input("\n请输入选项 (1-6): ").strip()
    
    try:
        if choice == "1":
            example_with_input_parser()
        elif choice == "2":
            example_with_reviewer()
        elif choice == "3":
            example_parse_and_review()
        elif choice == "4":
            example_single_step_parse()
        elif choice == "5":
            example_single_step_review()
        elif choice == "6":
            example_iterative_improvement()
        else:
            print("无效的选项！默认运行完整流程示例...")
            example_parse_and_review()
    except Exception as e:
        logger.error(f"运行示例时出错: {str(e)}")
        print(f"\n错误: {str(e)}")
        print("\n提示：请确保已配置 .env 文件中的 OPENAI_API_KEY")
