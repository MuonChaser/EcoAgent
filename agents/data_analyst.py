"""
智能体5：数据分析专家 - 支持读取本地数据并进行分析

该Agent具备以下能力:
1. 自动搜索并选择合适的数据集
2. 读取和预览本地数据文件
3. 获取数据统计信息
4. 执行数据查询和筛选
5. 结合LangChain工具链进行数据分析

使用建议:
- 在进行实证研究时，Agent会自动从RAG库中找到最相关的数据集
- 所有数据操作都会记录日志，便于追踪
"""

from typing import Dict, Any, Optional, List
from loguru import logger

from .base_agent import BaseAgent
from .schemas import DATA_ANALYST_SCHEMA
from prompts.data_analyst import SYSTEM_PROMPT, get_task_prompt

# 导入数据工具
try:
    from tools.data_storage import get_data_storage
    from tools.data_tools import get_data_tools, get_langchain_data_tools
    DATA_TOOLS_AVAILABLE = True
except ImportError:
    DATA_TOOLS_AVAILABLE = False
    logger.warning("[DataAnalyst] 数据工具未安装，数据读取功能将不可用")


class DataAnalystAgent(BaseAgent):
    """
    数据分析专家
    负责执行数据预处理、统计分析和模型估计
    支持自动搜索和读取本地数据
    """

    def __init__(
        self,
        custom_config: Optional[Dict[str, Any]] = None,
        data_storage_dir: str = "data/datasets"
    ):
        """
        初始化数据分析专家

        Args:
            custom_config: 自定义配置
            data_storage_dir: 数据存储目录
        """
        super().__init__("data_analyst", custom_config)

        # 初始化数据工具
        self.data_storage = None
        self.data_tools = None
        self.langchain_tools = None

        if DATA_TOOLS_AVAILABLE:
            try:
                self.data_storage = get_data_storage(data_storage_dir)
                self.data_tools = get_data_tools(self.data_storage)
                self.langchain_tools = get_langchain_data_tools(self.data_storage)
                logger.info(f"[DataAnalyst] 数据工具初始化完成，已注册 {len(self.langchain_tools)} 个工具")
            except Exception as e:
                logger.warning(f"[DataAnalyst] 数据工具初始化失败: {e}")

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def get_output_schema(self) -> Dict[str, Any]:
        return DATA_ANALYST_SCHEMA

    def get_task_prompt(self, **kwargs) -> str:
        research_topic = kwargs.get("research_topic", "")
        variable_system = kwargs.get("variable_system", "")
        theory_framework = kwargs.get("theory_framework", "")
        model_design = kwargs.get("model_design", "")
        data_info = kwargs.get("data_info", "")
        available_datasets = kwargs.get("available_datasets", "")

        # 如果有可用数据集信息，添加到data_info中
        if available_datasets:
            data_info = f"{data_info}\n\n## 可用数据集\n{available_datasets}"

        return get_task_prompt(
            research_topic=research_topic,
            variable_system=variable_system,
            theory_framework=theory_framework,
            model_design=model_design,
            data_info=data_info
        )

    # ==================== 数据搜索方法 ====================

    def search_data(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        搜索合适的数据集

        Args:
            query: 搜索查询，如"企业创新数据"
            n_results: 返回结果数

        Returns:
            匹配的数据集列表
        """
        if not self.data_tools:
            logger.warning("[DataAnalyst] 数据工具不可用")
            return []

        logger.info(f"[DataAnalyst] 搜索数据: {query}")
        return self.data_tools.search_datasets(query, n_results)

    def preview_dataset(self, file_path: str, n_rows: int = 10) -> Dict[str, Any]:
        """
        预览数据集

        Args:
            file_path: 数据文件路径
            n_rows: 预览行数

        Returns:
            数据预览信息
        """
        if not self.data_tools:
            logger.warning("[DataAnalyst] 数据工具不可用")
            return {}

        logger.info(f"[DataAnalyst] 预览数据: {file_path}")
        preview = self.data_tools.preview_data(file_path, n_rows)
        return preview.model_dump()

    def get_data_statistics(self, file_path: str) -> Dict[str, Any]:
        """
        获取数据统计信息

        Args:
            file_path: 数据文件路径

        Returns:
            统计信息
        """
        if not self.data_tools:
            logger.warning("[DataAnalyst] 数据工具不可用")
            return {}

        logger.info(f"[DataAnalyst] 获取统计: {file_path}")
        stats = self.data_tools.get_statistics(file_path, include_correlation=True)
        return stats.model_dump()

    def query_data(
        self,
        file_path: str,
        condition: Optional[str] = None,
        columns: Optional[List[str]] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        查询数据

        Args:
            file_path: 数据文件路径
            condition: 查询条件
            columns: 返回的列
            limit: 返回行数限制

        Returns:
            查询结果
        """
        if not self.data_tools:
            logger.warning("[DataAnalyst] 数据工具不可用")
            return {}

        logger.info(f"[DataAnalyst] 查询数据: {file_path}")
        result = self.data_tools.query_data(file_path, condition, columns, limit)
        return result.model_dump()

    def get_available_datasets(self, research_topic: str = "", n_results: int = 5) -> str:
        """
        获取可用数据集的描述信息

        Args:
            research_topic: 研究主题，用于搜索相关数据集
            n_results: 返回结果数

        Returns:
            数据集描述字符串
        """
        if not self.data_tools:
            return "（数据工具不可用，请手动指定数据）"

        # 搜索相关数据集
        if research_topic:
            datasets = self.search_data(research_topic, n_results)
        else:
            # 列出所有数据集
            datasets = []
            if self.data_storage:
                items = self.data_storage.list_all(limit=n_results)
                for item in items:
                    datasets.append({
                        "id": item.id,
                        "name": item.name,
                        "description": item.description,
                        "file_path": item.file_path,
                        "row_count": item.row_count,
                        "column_count": item.column_count,
                        "columns": item.columns[:10] if item.columns else []
                    })

        if not datasets:
            return "（暂无可用数据集，请先导入数据）"

        # 格式化输出
        lines = []
        for d in datasets:
            line = f"- **{d['name']}** (ID: {d['id']})"
            if d.get('row_count'):
                line += f" [{d['row_count']}行 x {d.get('column_count', '?')}列]"
            lines.append(line)
            lines.append(f"  路径: {d['file_path']}")
            if d.get('description'):
                lines.append(f"  描述: {d['description'][:100]}...")
            if d.get('columns'):
                lines.append(f"  列: {', '.join(d['columns'][:8])}...")
            lines.append("")

        return "\n".join(lines)

    # ==================== 分析执行方法 ====================

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行数据分析任务

        会自动搜索相关数据集并添加到上下文中

        Args:
            input_data: 输入数据

        Returns:
            分析结果
        """
        logger.info(f"[DataAnalyst] 开始执行数据分析任务")

        # 获取可用数据集信息
        research_topic = input_data.get("research_topic", "")
        available_datasets = self.get_available_datasets(research_topic)

        # 添加数据集信息到输入
        input_data["available_datasets"] = available_datasets

        # 调用父类的run方法
        result = super().run(input_data)

        # 添加额外信息
        result["data_tools_available"] = self.data_tools is not None
        if self.data_storage:
            result["datasets_count"] = len(self.data_storage.index.get("items", {}))

        return result

    def run_with_data(
        self,
        input_data: Dict[str, Any],
        data_file: str
    ) -> Dict[str, Any]:
        """
        使用指定数据文件执行分析

        Args:
            input_data: 输入数据
            data_file: 数据文件路径

        Returns:
            分析结果
        """
        logger.info(f"[DataAnalyst] 使用指定数据文件: {data_file}")

        # 获取数据预览和统计
        data_info_parts = []

        if self.data_tools:
            try:
                # 预览数据
                preview = self.preview_dataset(data_file, n_rows=5)
                data_info_parts.append(f"## 数据预览\n")
                data_info_parts.append(f"- 文件: {data_file}")
                data_info_parts.append(f"- 行数: {preview.get('total_rows', 'N/A')}")
                data_info_parts.append(f"- 列数: {preview.get('total_columns', 'N/A')}")
                data_info_parts.append(f"- 列名: {', '.join(preview.get('columns', [])[:15])}")

                # 获取统计
                stats = self.get_data_statistics(data_file)
                if stats.get('numeric_stats'):
                    data_info_parts.append(f"\n## 数值变量统计")
                    for col, col_stats in list(stats['numeric_stats'].items())[:5]:
                        data_info_parts.append(
                            f"- {col}: 均值={col_stats.get('mean', 'N/A'):.4f}, "
                            f"标准差={col_stats.get('std', 'N/A'):.4f}"
                        )

            except Exception as e:
                logger.warning(f"[DataAnalyst] 获取数据信息失败: {e}")

        # 更新输入数据
        existing_data_info = input_data.get("data_info", "")
        input_data["data_info"] = existing_data_info + "\n\n" + "\n".join(data_info_parts)

        return self.run(input_data)

    def analyze_data(
        self,
        file_path: str,
        analysis_type: str = "descriptive",
        variables: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        对指定数据文件进行分析

        Args:
            file_path: 数据文件路径
            analysis_type: 分析类型 (descriptive, correlation, regression)
            variables: 要分析的变量列表

        Returns:
            分析结果
        """
        logger.info(f"[DataAnalyst] 分析数据: {file_path} (类型: {analysis_type})")

        if not self.data_tools:
            return {"error": "数据工具不可用"}

        # 获取数据预览
        preview = self.data_tools.preview_data(file_path)

        # 获取统计信息
        stats = self.data_tools.get_statistics(
            file_path,
            columns=variables,
            include_correlation=(analysis_type in ["correlation", "regression"])
        )

        return {
            "file_path": file_path,
            "analysis_type": analysis_type,
            "data_summary": {
                "rows": preview.total_rows,
                "columns": preview.total_columns,
                "column_names": preview.columns
            },
            "statistics": stats.model_dump()
        }

    def process_output(self, raw_output: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理输出"""
        result = super().process_output(raw_output, input_data)

        parsed = result.get("parsed_data", {})
        result["data_analysis"] = parsed
        result["research_topic"] = input_data.get("research_topic")

        return result
