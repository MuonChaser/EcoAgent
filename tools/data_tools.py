"""
数据交互工具 - 支持读取、预览和分析本地数据
Data Interaction Tools for reading, previewing and analyzing local data

这些工具被设计为可以被Agent直接调用，使用LangChain的工具封装。
Agent在分析任务中应该积极使用这些工具来获取真实数据。
"""

import json
from typing import List, Dict, Any, Optional, Union, Callable
from pathlib import Path
from pydantic import BaseModel, Field
from loguru import logger

# LangChain工具封装
try:
    from langchain.tools import tool, BaseTool
    from langchain_core.tools import ToolException
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logger.warning("langchain未安装，LangChain工具封装将不可用")
    # 定义占位符
    def tool(func):
        return func
    class BaseTool:
        pass
    class ToolException(Exception):
        pass

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("pandas未安装，数据工具功能将受限。请运行: pip install pandas numpy")

# 导入数据存储工具
from tools.data_storage import DataStorageTool, get_data_storage


# ==================== 数据模型 ====================

class DataPreview(BaseModel):
    """数据预览结果"""
    file_path: str = Field(description="文件路径")
    total_rows: int = Field(description="总行数")
    total_columns: int = Field(description="总列数")
    columns: List[str] = Field(description="列名列表")
    dtypes: Dict[str, str] = Field(description="列类型")
    head: List[Dict[str, Any]] = Field(description="前几行数据")
    memory_usage: str = Field(description="内存使用")


class DataStatistics(BaseModel):
    """数据统计结果"""
    file_path: str = Field(description="文件路径")
    numeric_stats: Dict[str, Dict[str, float]] = Field(description="数值列统计")
    categorical_stats: Dict[str, Dict[str, Any]] = Field(description="分类列统计")
    missing_stats: Dict[str, Dict[str, Any]] = Field(description="缺失值统计")
    correlation_matrix: Optional[Dict[str, Dict[str, float]]] = Field(default=None, description="相关系数矩阵")


class DataQueryResult(BaseModel):
    """数据查询结果"""
    file_path: str = Field(description="文件路径")
    query: str = Field(description="查询条件")
    total_matched: int = Field(description="匹配行数")
    data: List[Dict[str, Any]] = Field(description="查询结果")
    columns: List[str] = Field(description="返回的列")


# ==================== 核心数据工具类 ====================

class DataTools:
    """
    数据交互工具集

    提供以下功能:
    1. 读取数据文件 (CSV, Excel, JSON, Parquet)
    2. 数据预览 (head, tail, sample)
    3. 数据统计 (describe, value_counts)
    4. 数据查询 (filter, select)
    5. 数据导出 (subset导出)

    使用建议:
    - Agent在需要分析数据时，应该首先使用search_datasets找到合适的数据
    - 然后使用preview_data了解数据结构
    - 再使用get_statistics获取统计信息
    - 最后使用query_data进行具体的数据查询

    所有操作都会在日志中记录，便于追踪Agent的数据使用情况。
    """

    def __init__(self, data_storage: Optional[DataStorageTool] = None):
        """
        初始化数据工具

        Args:
            data_storage: 数据存储工具实例，用于查找数据集
        """
        self.data_storage = data_storage or get_data_storage()
        self._cache: Dict[str, pd.DataFrame] = {}  # 简单缓存
        logger.info("[DataTools] 数据工具初始化完成")

    def _read_file(self, file_path: str, use_cache: bool = True) -> pd.DataFrame:
        """
        读取数据文件

        Args:
            file_path: 文件路径
            use_cache: 是否使用缓存

        Returns:
            DataFrame
        """
        if not PANDAS_AVAILABLE:
            raise ToolException("pandas未安装，无法读取数据文件")

        # 检查缓存
        if use_cache and file_path in self._cache:
            logger.debug(f"[DataTools] 使用缓存: {file_path}")
            return self._cache[file_path]

        path = Path(file_path)
        if not path.exists():
            raise ToolException(f"文件不存在: {file_path}")

        logger.info(f"[DataTools] 读取数据文件: {file_path}")

        try:
            suffix = path.suffix.lower()
            if suffix == '.csv':
                df = pd.read_csv(file_path, encoding='utf-8-sig')
            elif suffix in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            elif suffix == '.json':
                df = pd.read_json(file_path)
            elif suffix == '.parquet':
                df = pd.read_parquet(file_path)
            else:
                raise ToolException(f"不支持的文件格式: {suffix}")

            # 缓存（限制大小）
            if use_cache and len(df) < 100000:  # 只缓存小于10万行的数据
                self._cache[file_path] = df

            logger.info(f"[DataTools] 成功读取数据: {len(df)}行 x {len(df.columns)}列")
            return df

        except Exception as e:
            logger.error(f"[DataTools] 读取数据失败: {e}")
            raise ToolException(f"读取数据失败: {e}")

    def search_datasets(
        self,
        query: str,
        n_results: int = 5,
        search_type: str = "hybrid"
    ) -> List[Dict[str, Any]]:
        """
        搜索合适的数据集

        使用自然语言描述你需要的数据，系统会返回最匹配的数据集。

        Args:
            query: 自然语言查询，如 "企业创新相关数据" 或 "省级面板数据"
            n_results: 返回结果数量
            search_type: 搜索类型 (semantic/keyword/hybrid)

        Returns:
            匹配的数据集列表

        Example:
            >>> tools.search_datasets("需要企业研发投入相关的数据")
            >>> tools.search_datasets("包含GDP的省级数据", n_results=3)
        """
        logger.info(f"[DataTools] 搜索数据集: {query}")

        if search_type == "semantic":
            result = self.data_storage.search_semantic(query, n_results)
        elif search_type == "keyword":
            result = self.data_storage.search_keyword(query, n_results=n_results)
        else:
            result = self.data_storage.search_hybrid(query, n_results)

        # 转换为简单字典列表
        datasets = []
        for item in result.items:
            datasets.append({
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "file_path": item.file_path,
                "row_count": item.row_count,
                "column_count": item.column_count,
                "columns": item.columns[:20] if item.columns else [],  # 限制列数
                "domain": item.domain,
                "keywords": item.keywords
            })

        logger.info(f"[DataTools] 找到 {len(datasets)} 个匹配数据集")
        return datasets

    def preview_data(
        self,
        file_path: str,
        n_rows: int = 10,
        preview_type: str = "head"
    ) -> DataPreview:
        """
        预览数据文件

        在分析数据之前，先预览数据结构是很重要的。

        Args:
            file_path: 数据文件路径
            n_rows: 预览行数 (默认10行)
            preview_type: 预览类型 (head/tail/sample)

        Returns:
            数据预览结果

        Example:
            >>> preview = tools.preview_data("/path/to/data.csv")
            >>> print(preview.columns)
            >>> print(preview.head)
        """
        logger.info(f"[DataTools] 预览数据: {file_path} (类型: {preview_type}, 行数: {n_rows})")

        df = self._read_file(file_path)

        # 获取预览数据
        if preview_type == "head":
            preview_df = df.head(n_rows)
        elif preview_type == "tail":
            preview_df = df.tail(n_rows)
        elif preview_type == "sample":
            preview_df = df.sample(min(n_rows, len(df)))
        else:
            preview_df = df.head(n_rows)

        # 转换为可序列化的格式
        head_data = preview_df.replace({np.nan: None}).to_dict('records')

        # 计算内存使用
        memory = df.memory_usage(deep=True).sum()
        if memory > 1024 * 1024:
            memory_str = f"{memory / (1024 * 1024):.2f} MB"
        else:
            memory_str = f"{memory / 1024:.2f} KB"

        result = DataPreview(
            file_path=file_path,
            total_rows=len(df),
            total_columns=len(df.columns),
            columns=list(df.columns),
            dtypes={col: str(dtype) for col, dtype in df.dtypes.items()},
            head=head_data,
            memory_usage=memory_str
        )

        logger.info(f"[DataTools] 预览完成: {len(df)}行 x {len(df.columns)}列")
        return result

    def get_statistics(
        self,
        file_path: str,
        columns: Optional[List[str]] = None,
        include_correlation: bool = False
    ) -> DataStatistics:
        """
        获取数据统计信息

        获取数值列的描述性统计和分类列的频数统计。

        Args:
            file_path: 数据文件路径
            columns: 指定统计的列 (默认全部)
            include_correlation: 是否包含相关系数矩阵

        Returns:
            数据统计结果

        Example:
            >>> stats = tools.get_statistics("/path/to/data.csv")
            >>> print(stats.numeric_stats)  # 数值统计
            >>> print(stats.missing_stats)  # 缺失值统计
        """
        logger.info(f"[DataTools] 获取统计信息: {file_path}")

        df = self._read_file(file_path)

        if columns:
            df = df[columns]

        # 数值列统计
        numeric_cols = df.select_dtypes(include=['number']).columns
        numeric_stats = {}
        for col in numeric_cols:
            try:
                desc = df[col].describe()
                numeric_stats[col] = {
                    'count': int(desc['count']),
                    'mean': float(desc['mean']),
                    'std': float(desc['std']),
                    'min': float(desc['min']),
                    '25%': float(desc['25%']),
                    '50%': float(desc['50%']),
                    '75%': float(desc['75%']),
                    'max': float(desc['max'])
                }
            except Exception:
                pass

        # 分类列统计
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        categorical_stats = {}
        for col in categorical_cols:
            try:
                value_counts = df[col].value_counts().head(10)
                categorical_stats[col] = {
                    'unique_count': int(df[col].nunique()),
                    'top_values': value_counts.to_dict(),
                    'most_common': str(df[col].mode().iloc[0]) if len(df[col].mode()) > 0 else None
                }
            except Exception:
                pass

        # 缺失值统计
        missing_stats = {}
        for col in df.columns:
            missing_count = int(df[col].isna().sum())
            missing_stats[col] = {
                'missing_count': missing_count,
                'missing_ratio': round(missing_count / len(df), 4) if len(df) > 0 else 0,
                'non_missing_count': len(df) - missing_count
            }

        # 相关系数矩阵
        correlation_matrix = None
        if include_correlation and len(numeric_cols) > 1:
            try:
                corr = df[numeric_cols].corr()
                correlation_matrix = {
                    col: {c: round(v, 4) for c, v in row.items()}
                    for col, row in corr.to_dict().items()
                }
            except Exception:
                pass

        result = DataStatistics(
            file_path=file_path,
            numeric_stats=numeric_stats,
            categorical_stats=categorical_stats,
            missing_stats=missing_stats,
            correlation_matrix=correlation_matrix
        )

        logger.info(f"[DataTools] 统计完成: {len(numeric_stats)}个数值列, {len(categorical_stats)}个分类列")
        return result

    def query_data(
        self,
        file_path: str,
        condition: Optional[str] = None,
        columns: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> DataQueryResult:
        """
        查询数据

        使用pandas query语法筛选数据。

        Args:
            file_path: 数据文件路径
            condition: 查询条件 (pandas query语法)，如 "age > 30 and salary > 50000"
            columns: 返回的列 (默认全部)
            limit: 返回行数限制
            offset: 偏移量

        Returns:
            查询结果

        Example:
            >>> result = tools.query_data(
            ...     "/path/to/data.csv",
            ...     condition="year >= 2020",
            ...     columns=["company", "revenue", "year"],
            ...     limit=50
            ... )
            >>> print(result.data)
        """
        logger.info(f"[DataTools] 查询数据: {file_path}, 条件: {condition}")

        df = self._read_file(file_path)

        # 应用查询条件
        if condition:
            try:
                df = df.query(condition)
                logger.info(f"[DataTools] 条件筛选后: {len(df)}行")
            except Exception as e:
                logger.warning(f"[DataTools] 查询条件执行失败: {e}")
                # 尝试更宽松的解析
                raise ToolException(f"查询条件语法错误: {e}")

        # 选择列
        return_columns = columns if columns else list(df.columns)
        if columns:
            available_cols = [c for c in columns if c in df.columns]
            if available_cols:
                df = df[available_cols]
                return_columns = available_cols

        # 分页
        total_matched = len(df)
        df = df.iloc[offset:offset + limit]

        # 转换数据
        data = df.replace({np.nan: None}).to_dict('records')

        result = DataQueryResult(
            file_path=file_path,
            query=condition or "无条件",
            total_matched=total_matched,
            data=data,
            columns=return_columns
        )

        logger.info(f"[DataTools] 查询完成: 匹配 {total_matched}行, 返回 {len(data)}行")
        return result

    def get_column_values(
        self,
        file_path: str,
        column: str,
        unique: bool = True,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        获取列的值

        Args:
            file_path: 数据文件路径
            column: 列名
            unique: 是否只返回唯一值
            limit: 返回数量限制

        Returns:
            列值信息
        """
        logger.info(f"[DataTools] 获取列值: {file_path} - {column}")

        df = self._read_file(file_path)

        if column not in df.columns:
            raise ToolException(f"列不存在: {column}")

        if unique:
            values = df[column].dropna().unique().tolist()[:limit]
        else:
            values = df[column].dropna().tolist()[:limit]

        result = {
            "column": column,
            "dtype": str(df[column].dtype),
            "total_count": len(df),
            "unique_count": df[column].nunique(),
            "missing_count": int(df[column].isna().sum()),
            "values": [str(v) if not isinstance(v, (int, float, bool)) else v for v in values]
        }

        logger.info(f"[DataTools] 获取列值完成: {column}, {len(values)}个值")
        return result

    def export_subset(
        self,
        file_path: str,
        output_path: str,
        condition: Optional[str] = None,
        columns: Optional[List[str]] = None
    ) -> str:
        """
        导出数据子集

        Args:
            file_path: 源数据文件路径
            output_path: 输出文件路径
            condition: 筛选条件
            columns: 导出的列

        Returns:
            输出文件路径
        """
        logger.info(f"[DataTools] 导出数据子集: {file_path} -> {output_path}")

        df = self._read_file(file_path)

        if condition:
            df = df.query(condition)

        if columns:
            available_cols = [c for c in columns if c in df.columns]
            df = df[available_cols]

        # 根据输出格式保存
        output_suffix = Path(output_path).suffix.lower()
        if output_suffix == '.csv':
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
        elif output_suffix in ['.xlsx', '.xls']:
            df.to_excel(output_path, index=False)
        elif output_suffix == '.json':
            df.to_json(output_path, orient='records', force_ascii=False, indent=2)
        elif output_suffix == '.parquet':
            df.to_parquet(output_path, index=False)
        else:
            df.to_csv(output_path, index=False, encoding='utf-8-sig')

        logger.info(f"[DataTools] 导出完成: {len(df)}行 -> {output_path}")
        return output_path

    def clear_cache(self):
        """清除数据缓存"""
        self._cache.clear()
        logger.info("[DataTools] 缓存已清除")


# ==================== LangChain 工具封装 ====================

def create_data_tools(data_storage: Optional[DataStorageTool] = None) -> List[BaseTool]:
    """
    创建LangChain格式的数据工具列表

    这些工具可以直接被LangChain Agent使用。
    Agent应该积极使用这些工具来获取和分析真实数据。

    Args:
        data_storage: 数据存储工具实例

    Returns:
        LangChain工具列表
    """
    tools_instance = DataTools(data_storage)

    @tool
    def search_datasets(query: str, n_results: int = 5) -> str:
        """
        搜索合适的数据集。使用自然语言描述你需要的数据。

        强烈建议在进行数据分析前先使用此工具找到合适的数据集。

        Args:
            query: 数据需求描述，如"企业创新相关数据"或"省级GDP面板数据"
            n_results: 返回结果数量

        Returns:
            匹配的数据集列表(JSON格式)

        Example:
            search_datasets("需要企业研发投入相关的数据")
        """
        logger.info(f"[LangChain Tool] search_datasets: {query}")
        results = tools_instance.search_datasets(query, n_results)
        return json.dumps(results, ensure_ascii=False, indent=2)

    @tool
    def preview_data(file_path: str, n_rows: int = 10) -> str:
        """
        预览数据文件的结构和前几行内容。

        在分析数据之前，应该先预览了解数据结构。

        Args:
            file_path: 数据文件的完整路径
            n_rows: 预览的行数

        Returns:
            数据预览信息(JSON格式)，包含列名、类型、前几行数据等
        """
        logger.info(f"[LangChain Tool] preview_data: {file_path}")
        result = tools_instance.preview_data(file_path, n_rows)
        return result.model_dump_json(indent=2)

    @tool
    def get_data_statistics(file_path: str, include_correlation: bool = False) -> str:
        """
        获取数据的统计信息。

        获取数值列的均值、标准差、最大最小值等统计量，
        以及分类列的频数统计和缺失值情况。

        Args:
            file_path: 数据文件的完整路径
            include_correlation: 是否计算相关系数矩阵

        Returns:
            统计信息(JSON格式)
        """
        logger.info(f"[LangChain Tool] get_data_statistics: {file_path}")
        result = tools_instance.get_statistics(file_path, include_correlation=include_correlation)
        return result.model_dump_json(indent=2)

    @tool
    def query_data(file_path: str, condition: str = "", columns: str = "", limit: int = 100) -> str:
        """
        查询和筛选数据。

        使用pandas query语法筛选数据，获取满足条件的数据子集。

        Args:
            file_path: 数据文件的完整路径
            condition: 查询条件，如"year >= 2020 and revenue > 1000000"
            columns: 需要返回的列，用逗号分隔，如"company,year,revenue"
            limit: 返回的最大行数

        Returns:
            查询结果(JSON格式)

        Example:
            query_data("/path/data.csv", "year >= 2020", "company,revenue", 50)
        """
        logger.info(f"[LangChain Tool] query_data: {file_path}, condition={condition}")
        cols = [c.strip() for c in columns.split(',')] if columns else None
        cond = condition if condition else None
        result = tools_instance.query_data(file_path, cond, cols, limit)
        return result.model_dump_json(indent=2)

    @tool
    def get_column_info(file_path: str, column: str) -> str:
        """
        获取指定列的详细信息和值分布。

        Args:
            file_path: 数据文件的完整路径
            column: 列名

        Returns:
            列信息(JSON格式)
        """
        logger.info(f"[LangChain Tool] get_column_info: {file_path} - {column}")
        result = tools_instance.get_column_values(file_path, column, unique=True, limit=50)
        return json.dumps(result, ensure_ascii=False, indent=2)

    return [search_datasets, preview_data, get_data_statistics, query_data, get_column_info]


# ==================== 便捷函数 ====================

def get_data_tools(data_storage: Optional[DataStorageTool] = None) -> DataTools:
    """
    获取数据工具实例

    Args:
        data_storage: 数据存储工具实例

    Returns:
        数据工具实例
    """
    return DataTools(data_storage)


def get_langchain_data_tools(data_storage: Optional[DataStorageTool] = None) -> List[BaseTool]:
    """
    获取LangChain格式的数据工具

    这些工具可以被直接添加到LangChain Agent中使用。
    Agent应该积极使用这些工具进行数据分析任务。

    Args:
        data_storage: 数据存储工具实例

    Returns:
        LangChain工具列表
    """
    return create_data_tools(data_storage)
