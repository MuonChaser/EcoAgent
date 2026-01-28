"""
智能体1：文献搜集专家
"""
from typing import Dict, Any, List
from langchain_core.tools import Tool
from loguru import logger

from .tool_agent import ToolAgent
from prompts.literature_collector import SYSTEM_PROMPT, get_task_prompt

# 导入文献存储工具
try:
    from tools.literature_storage import get_literature_storage, LiteratureStorageTool
    LITERATURE_STORAGE_AVAILABLE = True
except ImportError:
    LITERATURE_STORAGE_AVAILABLE = False
    logger.warning("文献存储工具不可用")


class LiteratureCollectorAgent(ToolAgent):
    """
    文献搜集专家
    负责搜集和分析经济学文献

    支持：
    1. 从本地文献数据库检索已有文献（优先）
    2. 如果本地数据库没有足够文献，则通过LLM生成
    """

    def __init__(
        self,
        custom_config: Dict[str, Any] = None,
        literature_storage_dir: str = "data/literature"
    ):
        self.literature_storage_dir = literature_storage_dir
        self.literature_storage = None

        # 初始化文献存储
        if LITERATURE_STORAGE_AVAILABLE:
            try:
                self.literature_storage = get_literature_storage(literature_storage_dir)
                stats = self.literature_storage.get_statistics()
                logger.info(f"文献数据库已连接，共 {stats['total_count']} 篇文献")
            except Exception as e:
                logger.warning(f"文献存储初始化失败: {e}")

        super().__init__("literature_collector", custom_config)

    def get_tools(self) -> List[Tool]:
        """获取可用工具"""
        tools = []

        if self.literature_storage:
            # 语义搜索工具
            def search_semantic_wrapper(query: str) -> str:
                """语义搜索包装函数"""
                # 处理可能的 n_results 参数（从 query 中解析）
                # 默认返回 10 个结果
                return self._search_literature_semantic(query, 10)

            tools.append(Tool(
                name="search_literature_semantic",
                description="""在本地文献数据库中进行语义搜索。

                输入: 搜索查询（中文或英文），如"数字化转型对企业创新的影响"

                返回: 匹配的文献列表，包含标题、作者、年份、期刊、摘要、变量定义、核心结论等信息。

                使用场景: 当需要搜索特定主题的文献时，使用此工具先检查本地数据库。

                示例: search_literature_semantic("环境监管对企业生产率的影响")""",
                func=search_semantic_wrapper
            ))

            # 关键词搜索工具
            def search_keyword_wrapper(keyword: str) -> str:
                """关键词搜索包装函数"""
                return self._search_literature_keyword(keyword, 10)

            tools.append(Tool(
                name="search_literature_keyword",
                description="""在本地文献数据库中进行关键词搜索。

                输入: 关键词（中文或英文），如"全要素生产率"

                返回: 包含该关键词的文献列表。

                使用场景: 当需要精确匹配某个关键词时使用。

                示例: search_literature_keyword("TFP")""",
                func=search_keyword_wrapper
            ))

            # 统计信息工具
            def get_stats_wrapper(query: str = "") -> str:
                """获取统计信息包装函数"""
                stats = self.literature_storage.get_statistics()
                # 格式化为易读的字符串
                output = f"""本地文献数据库统计:
- 总文献数: {stats['total_count']}
- 数据库路径: {stats['storage_path']}
- 向量搜索: {'可用' if stats['chroma_available'] else '不可用'}
- 嵌入模型: {stats['embedding_model']}

按年份分布:
"""
                for year, count in sorted(stats['by_year'].items(), reverse=True)[:10]:
                    output += f"  - {year}: {count} 篇\n"

                if stats['by_journal']:
                    output += "\n主要期刊:\n"
                    # 按数量排序，取前10个
                    top_journals = sorted(stats['by_journal'].items(), key=lambda x: x[1], reverse=True)[:10]
                    for journal, count in top_journals:
                        output += f"  - {journal}: {count} 篇\n"

                return output

            tools.append(Tool(
                name="get_literature_stats",
                description="""获取本地文献数据库的统计信息。

                输入: 无需参数（可以传入任意字符串或留空）

                返回: 总文献数、按年份分布、按期刊分布等统计信息。

                使用场景: 了解数据库现状，决定是否需要补充文献。

                示例: get_literature_stats("")""",
                func=get_stats_wrapper
            ))

        return tools

    def _search_literature_semantic(self, query: str, n_results: int = 10) -> str:
        """语义搜索文献"""
        try:
            result = self.literature_storage.search_semantic(query, n_results)

            if not result.items:
                return f"在本地数据库中未找到与'{query}'相关的文献。"

            # 格式化结果
            output_lines = [f"找到 {len(result.items)} 篇相关文献：\n"]
            for i, item in enumerate(result.items, 1):
                output_lines.append(f"{i}. {item.authors} ({item.year}). {item.title}")
                if item.journal:
                    output_lines.append(f"   期刊: {item.journal}")
                if item.core_conclusion:
                    output_lines.append(f"   核心结论: {item.core_conclusion}")
                if item.variable_x_definition:
                    output_lines.append(f"   X变量: {item.variable_x_definition}")
                if item.variable_y_definition:
                    output_lines.append(f"   Y变量: {item.variable_y_definition}")
                if item.theoretical_mechanism:
                    output_lines.append(f"   理论机制: {', '.join(item.theoretical_mechanism)}")
                if item.identification_strategy:
                    output_lines.append(f"   识别策略: {item.identification_strategy}")
                output_lines.append("")

            return "\n".join(output_lines)

        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            return f"搜索失败: {str(e)}"

    def _search_literature_keyword(self, keyword: str, n_results: int = 10) -> str:
        """关键词搜索文献"""
        try:
            result = self.literature_storage.search_keyword(keyword, n_results=n_results)

            if not result.items:
                return f"在本地数据库中未找到包含关键词'{keyword}'的文献。"

            # 格式化结果
            output_lines = [f"找到 {len(result.items)} 篇包含关键词'{keyword}'的文献：\n"]
            for i, item in enumerate(result.items, 1):
                output_lines.append(f"{i}. {item.authors} ({item.year}). {item.title}")
                if item.journal:
                    output_lines.append(f"   期刊: {item.journal}")
                output_lines.append("")

            return "\n".join(output_lines)

        except Exception as e:
            logger.error(f"关键词搜索失败: {e}")
            return f"搜索失败: {str(e)}"

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT
    
    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "literature_list": {
                    "type": "array",
                    "description": "文献列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "number", "description": "序号"},
                            "authors": {"type": "string", "description": "作者"},
                            "year": {"type": "number", "description": "年份"},
                            "title": {"type": "string", "description": "论文标题"},
                            "journal": {"type": "string", "description": "期刊名称"},
                            "variable_x": {
                                "type": "object",
                                "properties": {
                                    "definition": {"type": "string", "description": "X的定义"},
                                    "measurement": {"type": "string", "description": "X的衡量方式"}
                                }
                            },
                            "variable_y": {
                                "type": "object",
                                "properties": {
                                    "definition": {"type": "string", "description": "Y的定义"},
                                    "measurement": {"type": "string", "description": "Y的衡量方式"}
                                }
                            },
                            "core_conclusion": {"type": "string", "description": "核心结论（量化）"},
                            "theoretical_mechanism": {"type": "array", "items": {"type": "string"}, "description": "理论机制列表"},
                            "data_source": {"type": "string", "description": "数据来源"},
                            "heterogeneity_dimensions": {"type": "array", "items": {"type": "string"}, "description": "异质性维度"},
                            "identification_strategy": {"type": "string", "description": "识别策略"},
                            "limitations": {"type": "array", "items": {"type": "string"}, "description": "研究不足"}
                        },
                        "required": ["id", "authors", "year", "title", "journal"]
                    }
                },
                "summary": {
                    "type": "object",
                    "properties": {
                        "total_papers": {"type": "number", "description": "总文献数"},
                        "main_findings": {"type": "array", "items": {"type": "string"}, "description": "主要发现"},
                        "research_gaps": {"type": "array", "items": {"type": "string"}, "description": "研究空白"}
                    }
                }
            },
            "required": ["literature_list"]
        }
    
    def get_task_prompt(self, **kwargs) -> str:
        research_topic = kwargs.get("research_topic", "")
        keyword_group_a = kwargs.get("keyword_group_a", [])
        keyword_group_b = kwargs.get("keyword_group_b", [])
        min_papers = kwargs.get("min_papers", 10)

        return get_task_prompt(
            research_topic=research_topic,
            keyword_group_a=keyword_group_a,
            keyword_group_b=keyword_group_b,
            min_papers=min_papers
        )
    
    def process_output(self, raw_output: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        result = super().process_output(raw_output, input_data)
        
        parsed = result.get("parsed_data", {})
        result["literature_list"] = parsed.get("literature_list", [])
        result["literature_summary"] = parsed  # 保留完整的解析数据
        result["research_topic"] = input_data.get("research_topic")
        
        return result
