"""
文献管理智能体
Literature Manager Agent - 管理文献存储、检索和分析
"""

import json
from typing import Dict, Any, Optional, List, Union
from loguru import logger

from agents.base_agent import BaseAgent
from tools.literature_storage import (
    LiteratureStorageTool,
    StoredLiteratureItem,
    LiteratureSearchResult,
    get_literature_storage
)
from prompts.literature_manager import SYSTEM_PROMPT, get_task_prompt


class LiteratureManagerAgent(BaseAgent):
    """
    文献管理智能体

    功能:
    1. 解析文献文本并提取结构化信息
    2. 存储文献到RAG系统
    3. 语义搜索和关键词搜索
    4. 文献推荐
    5. 文献总结
    """

    def __init__(
        self,
        storage_dir: str = "data/literature",
        custom_config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化文献管理智能体

        Args:
            storage_dir: 文献存储目录
            custom_config: 自定义配置
        """
        # 使用默认配置或自定义配置
        config = custom_config or {}
        if "temperature" not in config:
            config["temperature"] = 0.3  # 低温度确保准确性

        super().__init__(agent_type="literature_manager", custom_config=config)

        # 初始化文献存储工具
        self.storage = LiteratureStorageTool(storage_dir=storage_dir)
        logger.info(f"文献管理智能体初始化完成，存储目录: {storage_dir}")

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return SYSTEM_PROMPT

    def get_task_prompt(self, **kwargs) -> str:
        """获取任务提示词"""
        operation = kwargs.get("operation", "default")
        return get_task_prompt(operation, **kwargs)

    def get_output_schema(self) -> Dict[str, Any]:
        """获取输出JSON Schema"""
        return {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "data": {"type": "object"},
                "message": {"type": "string"}
            }
        }

    # ==================== 核心功能 ====================

    def parse_literature(self, raw_text: str) -> Dict[str, Any]:
        """
        解析文献文本，提取结构化信息

        Args:
            raw_text: 原始文献文本（可以是引用、摘要、或混合文本）

        Returns:
            解析后的文献信息
        """
        result = self.run({
            "operation": "parse",
            "raw_text": raw_text
        })

        return result.get("parsed_data", {})

    def add_literature_manual(
        self,
        literature_info: Dict[str, Any],
        auto_parse: bool = False
    ) -> str:
        """
        手动添加文献

        Args:
            literature_info: 文献信息字典
            auto_parse: 是否使用LLM自动解析和规范化

        Returns:
            文献ID
        """
        if auto_parse:
            # 使用LLM规范化
            result = self.run({
                "operation": "add",
                "literature_info": literature_info
            })
            normalized_info = result.get("parsed_data", literature_info)
        else:
            normalized_info = literature_info

        # 存储到文献库
        item_id = self.storage.add_literature(normalized_info, source="manual")
        logger.info(f"手动添加文献成功: {item_id}")
        return item_id

    def add_literature_from_text(self, text: str) -> str:
        """
        从文本中解析并添加文献

        Args:
            text: 包含文献信息的文本

        Returns:
            文献ID
        """
        # 先解析
        parsed = self.parse_literature(text)

        # 再存储
        item_id = self.storage.add_literature(parsed, source="text_parse")
        logger.info(f"从文本添加文献成功: {item_id}")
        return item_id

    def search(
        self,
        query: str,
        search_type: str = "hybrid",
        n_results: int = 10,
        use_llm: bool = False
    ) -> LiteratureSearchResult:
        """
        搜索文献

        Args:
            query: 搜索查询
            search_type: 搜索类型 (semantic, keyword, hybrid)
            n_results: 返回结果数
            use_llm: 是否使用LLM增强搜索

        Returns:
            搜索结果
        """
        if use_llm:
            # 使用LLM分析搜索意图并生成关键词
            result = self.run({
                "operation": "search",
                "query": query,
                "context": str(self.storage.get_statistics())
            })
            enhanced_query = result.get("parsed_data", {})

            # 使用增强的关键词搜索
            keywords = enhanced_query.get("keywords_chinese", []) + \
                      enhanced_query.get("keywords_english", [])
            combined_query = query + " " + " ".join(keywords)
        else:
            combined_query = query

        # 执行搜索
        if search_type == "semantic":
            return self.storage.search_semantic(combined_query, n_results)
        elif search_type == "keyword":
            return self.storage.search_keyword(combined_query, n_results=n_results)
        else:
            return self.storage.search_hybrid(combined_query, n_results)

    def recommend(
        self,
        topic: str,
        existing_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        推荐相关文献

        Args:
            topic: 研究主题
            existing_ids: 已有文献ID列表

        Returns:
            推荐结果
        """
        # 获取已有文献信息
        existing_literature = []
        if existing_ids:
            for item_id in existing_ids:
                item = self.storage.get_literature(item_id)
                if item:
                    existing_literature.append({
                        "title": item.title,
                        "authors": item.authors,
                        "year": item.year
                    })

        result = self.run({
            "operation": "recommend",
            "topic": topic,
            "existing_literature": existing_literature
        })

        return result.get("parsed_data", {})

    def summarize(
        self,
        literature_ids: List[str] = None,
        focus: str = ""
    ) -> Dict[str, Any]:
        """
        总结文献

        Args:
            literature_ids: 要总结的文献ID列表（如果为空则总结全部）
            focus: 关注焦点

        Returns:
            总结结果
        """
        # 获取文献列表
        if literature_ids:
            literature_list = []
            for item_id in literature_ids:
                item = self.storage.get_literature(item_id)
                if item:
                    literature_list.append(item.model_dump())
        else:
            items = self.storage.list_all(limit=50)
            literature_list = [item.model_dump() for item in items]

        result = self.run({
            "operation": "summarize",
            "literature_list": literature_list,
            "focus": focus
        })

        return result.get("parsed_data", {})

    # ==================== 便捷方法 ====================

    def import_from_collector(
        self,
        collector_output: Dict[str, Any],
        project_name: str = None
    ) -> List[str]:
        """
        从LiteratureCollector输出导入文献

        Args:
            collector_output: LiteratureCollector的输出
            project_name: 项目名称

        Returns:
            导入的文献ID列表
        """
        return self.storage.import_from_literature_collector(
            collector_output,
            research_project=project_name
        )

    def get_literature(self, item_id: str) -> Optional[StoredLiteratureItem]:
        """获取单篇文献"""
        return self.storage.get_literature(item_id)

    def delete_literature(self, item_id: str) -> bool:
        """删除文献"""
        return self.storage.delete_literature(item_id)

    def update_literature(
        self,
        item_id: str,
        updates: Dict[str, Any]
    ) -> Optional[StoredLiteratureItem]:
        """更新文献"""
        return self.storage.update_literature(item_id, updates)

    def list_all(self, limit: int = 100) -> List[StoredLiteratureItem]:
        """列出所有文献"""
        return self.storage.list_all(limit=limit)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.storage.get_statistics()

    def export_to_json(self, output_file: str) -> str:
        """导出到JSON"""
        return self.storage.export_to_json(output_file)

    def import_from_json(self, input_file: str) -> int:
        """从JSON导入"""
        return self.storage.import_from_json(input_file)


# ==================== 便捷函数 ====================

def create_literature_manager(
    storage_dir: str = "data/literature"
) -> LiteratureManagerAgent:
    """
    创建文献管理智能体实例

    Args:
        storage_dir: 存储目录

    Returns:
        文献管理智能体实例
    """
    return LiteratureManagerAgent(storage_dir=storage_dir)
