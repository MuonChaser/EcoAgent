"""
使用示例
"""
from main import ResearchOrchestrator, SimplifiedOrchestrator
from loguru import logger


def example_full_pipeline():
    """
    示例：运行完整研究流程
    """
    # 创建编排器
    orchestrator = ResearchOrchestrator(output_dir="output")
    
    # 定义研究参数
    research_topic = "绿色债券的引入可以带来企业业绩的提升吗？——基于上市公司的证据"
    
    keyword_group_a = [
        "绿色债券",
        "Green Bond",
        "可持续债券",
        "Sustainable Bond",
        "ESG债券"
    ]
    
    keyword_group_b = [
        "企业业绩",
        "Firm Performance",
        "公司绩效",
        "Corporate Performance",
        "财务表现",
        "Financial Performance"
    ]
    
    # 运行完整流程
    results = orchestrator.run_full_pipeline(
        research_topic=research_topic,
        keyword_group_a=keyword_group_a,
        keyword_group_b=keyword_group_b,
        min_papers=10,
        word_count=8000,
    )
    
    print("\n" + "=" * 50)
    print("研究流程完成！")
    print("=" * 50)
    print(f"研究主题: {results['research_topic']}")
    print(f"报告路径: {results.get('report_path', 'N/A')}")
    print(f"JSON路径: {results.get('json_path', 'N/A')}")
    print("=" * 50)
    
    return results


def example_partial_pipeline():
    """
    示例：运行部分流程
    """
    orchestrator = ResearchOrchestrator(output_dir="output")
    
    # 只运行前三个步骤
    results = orchestrator.run_full_pipeline(
        research_topic="数字化转型对企业创新的影响研究",
        keyword_group_a=["数字化转型", "Digital Transformation"],
        keyword_group_b=["企业创新", "Innovation"],
        enable_steps=["literature", "variable", "theory"],  # 只启用前三步
    )
    
    print("\n部分流程完成！")
    print(f"已完成步骤: literature, variable, theory")
    
    return results


def example_single_step():
    """
    示例：运行单个步骤
    """
    orchestrator = ResearchOrchestrator(output_dir="output")
    
    # 只运行文献搜集
    result = orchestrator.run_single_step(
        step="literature",
        input_data={
            "research_topic": "人工智能在计量经济学中的应用",
            "keyword_group_a": ["人工智能", "AI", "机器学习"],
            "keyword_group_b": ["计量经济学", "Econometrics"],
            "min_papers": 10,
        }
    )
    
    print("\n单步骤完成！")
    print(f"文献摘要长度: {len(result.get('literature_summary', ''))}")
    
    return result


def example_simplified():
    """
    示例：使用简化接口
    """
    simple = SimplifiedOrchestrator()
    
    # 快速研究
    report_path = simple.quick_research(
        topic="碳交易市场对企业环境绩效的影响",
        keywords_a="碳交易,碳市场,排放权交易",
        keywords_b="环境绩效,环境表现,碳排放"
    )
    
    print("\n快速研究完成！")
    print(f"报告路径: {report_path}")
    
    return report_path


def example_custom_config():
    """
    示例：使用自定义配置
    """
    # 可以在创建智能体时传入自定义配置
    from agents import LiteratureCollectorAgent
    
    custom_agent = LiteratureCollectorAgent(
        custom_config={
            "temperature": 0.2,  # 更低的温度
            "model": "gpt-4",    # 指定模型
        }
    )
    
    result = custom_agent.run({
        "research_topic": "区块链技术在供应链金融中的应用",
        "keyword_group_a": ["区块链", "Blockchain"],
        "keyword_group_b": ["供应链金融", "Supply Chain Finance"],
        "min_papers": 5,
    })
    
    print("\n自定义配置智能体运行完成！")
    
    return result


if __name__ == "__main__":
    # 运行示例
    print("=" * 70)
    print("AI for Econometrics 多智能体系统 - 使用示例")
    print("=" * 70)
    
    # 选择要运行的示例
    print("\n请选择要运行的示例：")
    print("1. 完整研究流程")
    print("2. 部分研究流程")
    print("3. 单个步骤")
    print("4. 简化接口")
    print("5. 自定义配置")
    
    choice = input("\n请输入选项 (1-5): ").strip()
    
    try:
        if choice == "1":
            example_full_pipeline()
        elif choice == "2":
            example_partial_pipeline()
        elif choice == "3":
            example_single_step()
        elif choice == "4":
            example_simplified()
        elif choice == "5":
            example_custom_config()
        else:
            print("无效的选项！默认运行完整流程示例...")
            example_full_pipeline()
    except Exception as e:
        logger.error(f"运行示例时出错: {str(e)}")
        print(f"\n错误: {str(e)}")
        print("\n提示：请确保已配置 .env 文件中的 OPENAI_API_KEY")
