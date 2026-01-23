"""
测试 LangChain 增强集成功能
验证 PydanticOutputParser、Callbacks 和 ResearchMemory
"""

from agents import InputParserAgent
from memory import ResearchMemory
from langchain_openai import ChatOpenAI
from config.config import API_KEY, API_BASE


def test_pydantic_parser():
    """测试 Pydantic Output Parser"""
    print("\n" + "=" * 60)
    print("测试 1: Pydantic Output Parser")
    print("=" * 60)

    agent = InputParserAgent()

    # 验证 parser 已初始化
    assert agent.use_pydantic_parser, "Pydantic parser 应该被启用"
    assert agent.output_parser is not None, "Output parser 应该存在"

    print(f"✓ Pydantic Parser 已启用")
    print(f"✓ Schema 类: {agent.output_parser.pydantic_object.__name__}")


def test_callbacks():
    """测试 Callbacks"""
    print("\n" + "=" * 60)
    print("测试 2: Callbacks 追踪")
    print("=" * 60)

    agent = InputParserAgent()

    # 验证 callbacks 已初始化
    assert len(agent.callbacks) > 0, "应该至少有一个 callback"

    print(f"✓ Callbacks 数量: {len(agent.callbacks)}")
    print(f"✓ Callback 类型: {[type(cb).__name__ for cb in agent.callbacks]}")


def test_research_memory():
    """测试 ResearchMemory 系统"""
    print("\n" + "=" * 60)
    print("测试 3: ResearchMemory 系统")
    print("=" * 60)

    # 创建 LLM（用于 memory）
    llm = ChatOpenAI(
        model='qwen-plus',
        temperature=0.5,
        openai_api_key=API_KEY,
        openai_api_base=API_BASE
    )

    memory = ResearchMemory(llm, buffer_size=2)

    # 测试添加多个 agent 输出
    test_outputs = [
        {
            'agent_name': 'input_parser',
            'output': {
                'parsed_data': {
                    'research_topic': '数字化转型对企业创新的影响',
                    'variable_x': {'name': '数字化转型'},
                    'variable_y': {'name': '企业创新'}
                }
            }
        },
        {
            'agent_name': 'literature_collector',
            'output': {
                'parsed_data': {
                    'literature_list': [
                        {'title': 'Paper 1', 'authors': 'Author A'},
                        {'title': 'Paper 2', 'authors': 'Author B'}
                    ],
                    'summary': {'total_papers': 2}
                }
            }
        },
        {
            'agent_name': 'variable_designer',
            'output': {
                'parsed_data': {
                    'core_variables': {
                        'explanatory_variable_x': [{'name': 'X1'}],
                        'dependent_variable_y': [{'name': 'Y1'}]
                    },
                    'control_variables': [{'name': 'Control1'}]
                }
            }
        }
    ]

    # 添加到 memory
    for item in test_outputs:
        memory.add_agent_output(item['agent_name'], item['output'])

    # 验证 memory 状态
    stats = memory.get_stats()

    print(f"✓ Agent 历史数量: {stats['agent_history_count']}")
    print(f"✓ 摘要存储数量: {stats['summary_store_count']}")
    print(f"✓ Buffer 存储数量: {stats['buffer_store_count']}")
    print(f"✓ 结构化存储完成: {stats['structured_store_completed']}/5")

    # 测试获取上下文
    context = memory.get_context_for_agent('theory_designer')

    print(f"✓ 上下文长度: {len(context)} 字符")

    # 验证 buffer size 限制
    assert stats['buffer_store_count'] <= 2, f"Buffer 应该最多保留 2 个，实际: {stats['buffer_store_count']}"
    print(f"✓ Buffer size 限制正常工作")

    # 测试摘要生成
    summary = memory.get_summary()
    print(f"✓ 摘要生成成功 (长度: {len(summary)} 字符)")

    return memory


def test_integration():
    """集成测试：测试完整流程"""
    print("\n" + "=" * 60)
    print("测试 4: 集成测试（模拟简化工作流）")
    print("=" * 60)

    # 创建 memory
    llm = ChatOpenAI(
        model='qwen-plus',
        temperature=0.5,
        openai_api_key=API_KEY,
        openai_api_base=API_BASE
    )
    memory = ResearchMemory(llm, buffer_size=2)

    # 创建 agent
    agent = InputParserAgent()

    print(f"✓ Agent 使用 Pydantic Parser: {agent.use_pydantic_parser}")
    print(f"✓ Agent Callbacks 数量: {len(agent.callbacks)}")

    # 模拟添加输出到 memory
    mock_output = {
        'agent_type': 'input_parser',
        'parsed_data': {
            'research_topic': '测试主题',
            'variable_x': {'name': 'X'},
            'variable_y': {'name': 'Y'},
            'keywords': {
                'group_a_chinese': ['关键词1'],
                'group_b_chinese': ['关键词2']
            }
        }
    }

    memory.add_agent_output('input_parser', mock_output)

    # 获取上下文
    context = memory.get_context_for_agent('variable_designer')

    print(f"✓ 集成测试完成")
    print(f"  - Memory 中有 {len(memory.agent_history)} 个 agent 记录")
    print(f"  - 上下文可用于下一个 agent")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("LangChain 增强集成功能测试")
    print("=" * 60)

    try:
        test_pydantic_parser()
        test_callbacks()
        test_research_memory()
        test_integration()

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)

        print("\n已完成的功能：")
        print("  ✓ Pydantic Output Parser 集成")
        print("  ✓ Callbacks 追踪（Token 统计）")
        print("  ✓ ResearchMemory 系统（三层架构）")
        print("\n下一步：")
        print("  - 集成 Memory 到 Orchestrator")
        print("  - 修改 Prompts 支持上下文注入")
        print("  - 创建 LaTeX Formatter Agent")

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        raise


if __name__ == "__main__":
    main()
