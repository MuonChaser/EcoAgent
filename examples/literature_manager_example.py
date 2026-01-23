"""
文献管理系统使用示例
Literature Manager Usage Examples

运行前请先安装依赖:
pip install chromadb sentence-transformers
"""

import json
from pathlib import Path

# 添加项目根目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.literature_storage import LiteratureStorageTool, get_literature_storage
from agents.literature_manager import LiteratureManagerAgent, create_literature_manager


def example_1_basic_storage():
    """示例1: 基本文献存储和检索"""
    print("\n" + "="*60)
    print("示例1: 基本文献存储和检索")
    print("="*60)

    # 创建存储工具
    storage = get_literature_storage("data/literature")

    # 手动添加文献
    literature_1 = {
        "authors": "Brynjolfsson, E., Rock, D., & Syverson, C.",
        "year": 2019,
        "title": "Artificial Intelligence and the Modern Productivity Paradox",
        "journal": "American Economic Review",
        "abstract": "This paper examines the relationship between AI adoption and productivity growth.",
        "keywords": ["artificial intelligence", "productivity", "technology"],
        "core_conclusion": "IT资本每增加1个百分点，TFP提升约0.3%-0.5%",
        "theoretical_mechanism": ["技术互补性假说", "知识积累机制"],
        "identification_strategy": "Fixed Effects with Industry-Time Trends, IV",
        "data_source": "美国制造业企业面板数据",
        "tags": ["AI", "生产率", "技术进步"]
    }

    literature_2 = {
        "authors": "Acemoglu, D., & Restrepo, P.",
        "year": 2020,
        "title": "Robots and Jobs: Evidence from US Labor Markets",
        "journal": "Journal of Political Economy",
        "abstract": "We study the effect of industrial robots on US local labor markets.",
        "keywords": ["robots", "automation", "employment", "wages"],
        "core_conclusion": "每千名工人增加一个机器人，就业率下降0.2%",
        "theoretical_mechanism": ["任务替代效应", "生产率效应"],
        "identification_strategy": "Shift-share IV",
        "data_source": "美国县级面板数据",
        "tags": ["自动化", "就业", "机器人"]
    }

    literature_3 = {
        "authors": "戴亦一, 肖金利, 潘越",
        "year": 2021,
        "title": "数字化转型与企业创新——基于中国上市公司的实证研究",
        "journal": "经济研究",
        "abstract": "本文研究了数字化转型对企业创新的影响。",
        "keywords": ["数字化转型", "企业创新", "专利"],
        "core_conclusion": "数字化转型显著促进企业创新产出，效应为15%-20%",
        "theoretical_mechanism": ["资源配置优化", "信息不对称缓解", "知识溢出"],
        "identification_strategy": "双重差分法(DID)",
        "data_source": "中国A股上市公司数据",
        "tags": ["数字化", "创新", "中国"]
    }

    # 添加文献
    id1 = storage.add_literature(literature_1)
    id2 = storage.add_literature(literature_2)
    id3 = storage.add_literature(literature_3)

    print(f"\n已添加文献:")
    print(f"  - {id1}: {literature_1['title'][:40]}...")
    print(f"  - {id2}: {literature_2['title'][:40]}...")
    print(f"  - {id3}: {literature_3['title'][:40]}...")

    # 查看统计信息
    stats = storage.get_statistics()
    print(f"\n文献库统计:")
    print(f"  总数: {stats['total_count']}")
    print(f"  按年份: {stats['by_year']}")
    print(f"  RAG可用: {stats['chroma_available']}")

    return storage


def example_2_semantic_search(storage: LiteratureStorageTool):
    """示例2: 语义搜索"""
    print("\n" + "="*60)
    print("示例2: 语义搜索")
    print("="*60)

    # 语义搜索 - 中文查询
    query1 = "人工智能如何影响企业生产效率"
    print(f"\n查询: {query1}")
    results = storage.search_semantic(query1, n_results=5)
    print(f"找到 {results.total_count} 篇相关文献:")
    for item in results.items:
        print(f"  - [{item.year}] {item.title[:50]}...")

    # 语义搜索 - 英文查询
    query2 = "automation impact on employment"
    print(f"\n查询: {query2}")
    results = storage.search_semantic(query2, n_results=5)
    print(f"找到 {results.total_count} 篇相关文献:")
    for item in results.items:
        print(f"  - [{item.year}] {item.title[:50]}...")


def example_3_keyword_search(storage: LiteratureStorageTool):
    """示例3: 关键词搜索"""
    print("\n" + "="*60)
    print("示例3: 关键词搜索")
    print("="*60)

    # 关键词搜索
    keyword = "数字化"
    print(f"\n关键词: {keyword}")
    results = storage.search_keyword(keyword, n_results=5)
    print(f"找到 {results.total_count} 篇相关文献:")
    for item in results.items:
        print(f"  - [{item.year}] {item.title[:50]}...")


def example_4_hybrid_search(storage: LiteratureStorageTool):
    """示例4: 混合搜索"""
    print("\n" + "="*60)
    print("示例4: 混合搜索（语义+关键词）")
    print("="*60)

    query = "技术创新 生产率"
    print(f"\n查询: {query}")
    results = storage.search_hybrid(query, n_results=5)
    print(f"找到 {results.total_count} 篇相关文献:")
    for item in results.items:
        print(f"  - [{item.year}] {item.authors}: {item.title[:40]}...")


def example_5_export_import(storage: LiteratureStorageTool):
    """示例5: 导出和导入"""
    print("\n" + "="*60)
    print("示例5: 导出和导入")
    print("="*60)

    # 导出到JSON
    export_file = "data/literature/export_example.json"
    storage.export_to_json(export_file)
    print(f"\n已导出到: {export_file}")

    # 读取导出文件查看
    with open(export_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"导出的文献数量: {data['total_count']}")


def example_6_agent_operations():
    """示例6: 使用智能体进行高级操作"""
    print("\n" + "="*60)
    print("示例6: 使用LiteratureManagerAgent")
    print("="*60)

    # 注意: 此示例需要配置LLM API
    # 如果没有配置，可以跳过此示例

    try:
        # 创建文献管理智能体
        manager = create_literature_manager("data/literature")
        print("\n文献管理智能体已创建")

        # 手动添加文献（不使用LLM解析）
        new_lit = {
            "authors": "李晓阳, 张明",
            "year": 2022,
            "title": "金融科技与中小企业融资约束——来自中国的证据",
            "journal": "管理世界",
            "keywords": ["金融科技", "融资约束", "中小企业"],
            "core_conclusion": "金融科技发展显著缓解了中小企业融资约束",
            "tags": ["金融科技", "融资"]
        }

        item_id = manager.add_literature_manual(new_lit, auto_parse=False)
        print(f"已添加文献: {item_id}")

        # 搜索（不使用LLM增强）
        results = manager.search("金融科技", search_type="hybrid", use_llm=False)
        print(f"\n搜索 '金融科技' 结果: {results.total_count} 篇")

        # 获取统计信息
        stats = manager.get_statistics()
        print(f"当前文献库共有 {stats['total_count']} 篇文献")

    except Exception as e:
        print(f"\n智能体示例跳过（可能未配置LLM API）: {e}")


def example_7_import_from_collector():
    """示例7: 从LiteratureCollector输出导入"""
    print("\n" + "="*60)
    print("示例7: 从LiteratureCollector输出导入")
    print("="*60)

    storage = get_literature_storage("data/literature")

    # 模拟LiteratureCollector的输出格式
    collector_output = {
        "literature_list": [
            {
                "id": 1,
                "authors": "Goldfarb, A., & Tucker, C.",
                "year": 2019,
                "title": "Digital Economics",
                "journal": "Journal of Economic Literature",
                "variable_x": {
                    "definition": "数字技术采用程度",
                    "measurement": "企业IT投资占比"
                },
                "variable_y": {
                    "definition": "经济绩效",
                    "measurement": "TFP增长率"
                },
                "core_conclusion": "数字技术显著降低了交易成本",
                "theoretical_mechanism": ["搜索成本降低", "信息不对称缓解"],
                "data_source": "美国企业调查数据",
                "identification_strategy": "工具变量法",
                "heterogeneity_dimensions": ["企业规模", "行业"],
                "limitations": ["外部有效性", "度量误差"]
            },
            {
                "id": 2,
                "authors": "吴非, 胡慧芷",
                "year": 2023,
                "title": "数字金融与企业绿色创新",
                "journal": "经济研究",
                "variable_x": {
                    "definition": "数字金融发展水平",
                    "measurement": "北大数字普惠金融指数"
                },
                "variable_y": {
                    "definition": "企业绿色创新",
                    "measurement": "绿色专利申请数量"
                },
                "core_conclusion": "数字金融促进企业绿色创新，效应约12%",
                "theoretical_mechanism": ["融资约束缓解", "信息披露改善"],
                "data_source": "中国A股上市公司",
                "identification_strategy": "双重差分+工具变量",
                "heterogeneity_dimensions": ["产权性质", "地区"],
                "limitations": ["内生性问题"]
            }
        ],
        "summary": {
            "total_papers": 2,
            "main_findings": ["数字技术促进经济发展", "数字金融缓解融资约束"]
        }
    }

    # 导入
    ids = storage.import_from_literature_collector(
        collector_output,
        research_project="数字经济研究"
    )
    print(f"\n从LiteratureCollector导入 {len(ids)} 篇文献:")
    for item_id in ids:
        item = storage.get_literature(item_id)
        if item:
            print(f"  - {item_id}: {item.title[:40]}...")


def main():
    """运行所有示例"""
    print("\n" + "="*60)
    print("文献管理系统使用示例")
    print("="*60)

    # 示例1: 基本存储
    storage = example_1_basic_storage()

    # 示例2-4: 搜索功能
    example_2_semantic_search(storage)
    example_3_keyword_search(storage)
    example_4_hybrid_search(storage)

    # 示例5: 导出导入
    example_5_export_import(storage)

    # 示例6: 智能体操作（需要LLM API）
    example_6_agent_operations()

    # 示例7: 从Collector导入
    example_7_import_from_collector()

    print("\n" + "="*60)
    print("所有示例运行完成!")
    print("="*60)

    # 最终统计
    final_stats = storage.get_statistics()
    print(f"\n最终文献库统计:")
    print(f"  总文献数: {final_stats['total_count']}")
    print(f"  存储路径: {final_stats['storage_path']}")
    print(f"  RAG可用: {final_stats['chroma_available']}")


if __name__ == "__main__":
    main()
