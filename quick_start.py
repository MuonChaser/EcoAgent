"""
快速开始示例 - 使用阿里云通义千问
"""
from main import ResearchOrchestrator

print("=" * 70)
print("AI for Econometrics - 快速开始示例")
print("使用阿里云通义千问模型")
print("=" * 70)

# 创建编排器
orchestrator = ResearchOrchestrator(output_dir="output")

# 方式1: 自然语言输入（推荐）
print("\n【方式1：自然语言输入】")
print("只需要描述你的研究想法...")

user_input = "我想研究数字化转型对企业创新的影响"
print(f"输入: {user_input}")

try:
    results = orchestrator.run_full_pipeline(
        user_input=user_input,
        enable_steps=["input_parse", "literature", "variable"],  # 先运行前3步测试
        min_papers=5,  # 减少文献数量以加快速度
    )
    
    print("\n✅ 前3步完成！")
    print(f"研究主题: {results['research_topic']}")
    if 'parsed_input' in results:
        print(f"\n解析结果预览:\n{results['parsed_input'][:300]}...")
    print(f"\n完整结果已保存到: output/stages/")
    
except Exception as e:
    print(f"\n❌ 执行失败: {str(e)}")
    print("\n请检查：")
    print("1. .env 文件中的 DASHSCOPE_API_KEY 是否正确")
    print("2. 运行 'python test_qwen.py' 测试API连接")

print("\n" + "=" * 70)
print("提示：")
print("1. 可以在 .env 文件中切换不同的通义千问模型")
print("2. 运行完整流程: enable_steps=['input_parse', 'literature', 'variable', 'theory', 'model', 'analysis', 'report']")
print("3. 启用审稿: enable_review=True")
print("=" * 70)
