"""
工具模块 - 文献搜索工具
"""
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from loguru import logger


class LiteratureSearchTool:
    """
    文献搜索工具
    支持通过各种学术搜索引擎搜索文献
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def search_arxiv(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        搜索arXiv上的论文
        
        Args:
            query: 搜索关键词
            max_results: 最大结果数
            
        Returns:
            论文列表
        """
        try:
            import arxiv
            
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            papers = []
            for result in search.results():
                papers.append({
                    'title': result.title,
                    'authors': [author.name for author in result.authors],
                    'abstract': result.summary,
                    'published': result.published.strftime('%Y-%m-%d'),
                    'url': result.entry_id,
                    'pdf_url': result.pdf_url,
                })
            
            logger.info(f"从arXiv搜索到 {len(papers)} 篇论文")
            return papers
            
        except Exception as e:
            logger.error(f"arXiv搜索失败: {str(e)}")
            return []
    
    def search_google_scholar(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        搜索Google Scholar（需要配置代理或使用API）
        
        注意：这是一个示例实现，实际使用需要配置合适的搜索API
        
        Args:
            query: 搜索关键词
            max_results: 最大结果数
            
        Returns:
            论文列表
        """
        logger.warning("Google Scholar搜索需要配置API，当前返回空列表")
        return []
    
    def format_literature_info(self, papers: List[Dict[str, Any]]) -> str:
        """
        格式化文献信息为可读文本
        
        Args:
            papers: 论文列表
            
        Returns:
            格式化后的文本
        """
        if not papers:
            return "未找到相关文献"
        
        formatted = []
        for i, paper in enumerate(papers, 1):
            formatted.append(f"\n{i}. {paper.get('title', 'Unknown')}")
            formatted.append(f"   作者: {', '.join(paper.get('authors', ['Unknown']))}")
            formatted.append(f"   发表时间: {paper.get('published', 'Unknown')}")
            formatted.append(f"   链接: {paper.get('url', 'N/A')}")
            if 'abstract' in paper:
                abstract = paper['abstract'][:200] + "..." if len(paper['abstract']) > 200 else paper['abstract']
                formatted.append(f"   摘要: {abstract}")
        
        return "\n".join(formatted)


class DataProcessingTool:
    """
    数据处理工具
    """
    
    @staticmethod
    def clean_data(data: Any, method: str = "drop") -> Any:
        """
        数据清洗
        
        Args:
            data: 输入数据
            method: 清洗方法 ("drop", "fill", "interpolate")
            
        Returns:
            清洗后的数据
        """
        try:
            import pandas as pd
            
            if not isinstance(data, pd.DataFrame):
                logger.warning("数据不是DataFrame格式，跳过清洗")
                return data
            
            if method == "drop":
                cleaned = data.dropna()
            elif method == "fill":
                cleaned = data.fillna(data.mean())
            elif method == "interpolate":
                cleaned = data.interpolate()
            else:
                logger.warning(f"未知的清洗方法: {method}，返回原数据")
                return data
            
            logger.info(f"数据清洗完成，原始行数: {len(data)}, 清洗后: {len(cleaned)}")
            return cleaned
            
        except Exception as e:
            logger.error(f"数据清洗失败: {str(e)}")
            return data
    
    @staticmethod
    def winsorize_data(data: Any, limits: tuple = (0.01, 0.01)) -> Any:
        """
        数据缩尾处理
        
        Args:
            data: 输入数据
            limits: 缩尾比例 (lower, upper)
            
        Returns:
            处理后的数据
        """
        try:
            import pandas as pd
            from scipy.stats.mstats import winsorize
            
            if not isinstance(data, pd.DataFrame):
                logger.warning("数据不是DataFrame格式，跳过缩尾")
                return data
            
            result = data.copy()
            for col in result.select_dtypes(include=['float64', 'int64']).columns:
                result[col] = winsorize(result[col], limits=limits)
            
            logger.info(f"数据缩尾处理完成，缩尾比例: {limits}")
            return result
            
        except Exception as e:
            logger.error(f"数据缩尾失败: {str(e)}")
            return data
    
    @staticmethod
    def standardize_data(data: Any) -> Any:
        """
        数据标准化
        
        Args:
            data: 输入数据
            
        Returns:
            标准化后的数据
        """
        try:
            import pandas as pd
            
            if not isinstance(data, pd.DataFrame):
                logger.warning("数据不是DataFrame格式，跳过标准化")
                return data
            
            result = data.copy()
            numeric_cols = result.select_dtypes(include=['float64', 'int64']).columns
            result[numeric_cols] = (result[numeric_cols] - result[numeric_cols].mean()) / result[numeric_cols].std()
            
            logger.info("数据标准化完成")
            return result
            
        except Exception as e:
            logger.error(f"数据标准化失败: {str(e)}")
            return data


class StatisticalAnalysisTool:
    """
    统计分析工具
    """
    
    @staticmethod
    def descriptive_statistics(data: Any) -> Dict[str, Any]:
        """
        描述性统计
        
        Args:
            data: 输入数据
            
        Returns:
            统计结果
        """
        try:
            import pandas as pd
            
            if not isinstance(data, pd.DataFrame):
                logger.warning("数据不是DataFrame格式，无法进行描述性统计")
                return {}
            
            stats = data.describe().to_dict()
            logger.info("描述性统计完成")
            return stats
            
        except Exception as e:
            logger.error(f"描述性统计失败: {str(e)}")
            return {}
    
    @staticmethod
    def correlation_analysis(data: Any, method: str = "pearson") -> Any:
        """
        相关性分析
        
        Args:
            data: 输入数据
            method: 相关系数方法 ("pearson", "spearman", "kendall")
            
        Returns:
            相关系数矩阵
        """
        try:
            import pandas as pd
            
            if not isinstance(data, pd.DataFrame):
                logger.warning("数据不是DataFrame格式，无法进行相关性分析")
                return None
            
            corr = data.corr(method=method)
            logger.info(f"相关性分析完成，方法: {method}")
            return corr
            
        except Exception as e:
            logger.error(f"相关性分析失败: {str(e)}")
            return None
    
    @staticmethod
    def regression_analysis(y: Any, X: Any, model_type: str = "ols") -> Dict[str, Any]:
        """
        回归分析
        
        Args:
            y: 因变量
            X: 自变量
            model_type: 模型类型 ("ols", "logit", "probit")
            
        Returns:
            回归结果
        """
        try:
            import statsmodels.api as sm
            
            X_with_const = sm.add_constant(X)
            
            if model_type == "ols":
                model = sm.OLS(y, X_with_const)
            elif model_type == "logit":
                model = sm.Logit(y, X_with_const)
            elif model_type == "probit":
                model = sm.Probit(y, X_with_const)
            else:
                logger.warning(f"未知的模型类型: {model_type}，使用OLS")
                model = sm.OLS(y, X_with_const)
            
            results = model.fit()
            
            output = {
                'params': results.params.to_dict(),
                'pvalues': results.pvalues.to_dict(),
                'rsquared': getattr(results, 'rsquared', None),
                'summary': str(results.summary())
            }
            
            logger.info(f"回归分析完成，模型类型: {model_type}")
            return output
            
        except Exception as e:
            logger.error(f"回归分析失败: {str(e)}")
            return {}
