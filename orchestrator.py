"""
Main Orchestrator - Orchestrate and manage multi-agent workflows

Full pipeline: Complete research paper first, then conduct reviewer assessment
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
from loguru import logger

from agents import (
    InputParserAgent,
    LiteratureCollectorAgent,
    VariableDesignerAgent,
    TheoryDesignerAgent,
    ModelDesignerAgent,
    DataAnalystAgent,
    ReportWriterAgent,
    ReviewerAgent,
)
from tools import ReportGenerator

# Import data tools
try:
    from tools.data_storage import get_data_storage
    DATA_TOOLS_AVAILABLE = True
except ImportError:
    DATA_TOOLS_AVAILABLE = False
    logger.warning("Data tools unavailable, data analysis functionality will be limited")

# Import knowledge graph tools
try:
    from tools.methodology_graph import get_methodology_graph, MethodologyKnowledgeGraph
    from config.config import KNOWLEDGE_GRAPH_CONFIG
    KNOWLEDGE_GRAPH_AVAILABLE = True
except ImportError:
    KNOWLEDGE_GRAPH_AVAILABLE = False
    KNOWLEDGE_GRAPH_CONFIG = {"enabled": False}
    logger.warning("Knowledge graph tools unavailable, method recommendation functionality will be limited")


class ResearchOrchestrator:
    """
    Research Orchestrator
    Responsible for coordinating agents to complete the full research pipeline

    Full pipeline:
    1. Input parsing (optional)
    2. Literature collection
    3. Variable design
    4. Theory design
    5. Model design
    6. Data analysis (supports automatic local data search)
    7. Report writing
    8. Reviewer assessment (scoring at the end)
    """

    def __init__(
        self,
        output_dir: str = "output",
        data_storage_dir: str = "data/datasets",
        literature_storage_dir: str = "data/literature",
        knowledge_graph_dir: str = None,
    ):
        """
        Initialize orchestrator

        Args:
            output_dir: Output directory
            data_storage_dir: Data storage directory
            literature_storage_dir: Literature storage directory
            knowledge_graph_dir: Knowledge graph storage directory (uses config default if None)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.data_storage_dir = data_storage_dir
        self.literature_storage_dir = literature_storage_dir

        # Initialize all agents
        self.input_parser = InputParserAgent()
        self.literature_collector = LiteratureCollectorAgent(
            literature_storage_dir=literature_storage_dir
        )
        self.variable_designer = VariableDesignerAgent()
        self.theory_designer = TheoryDesignerAgent()
        self.model_designer = ModelDesignerAgent()
        self.data_analyst = DataAnalystAgent(data_storage_dir=data_storage_dir)
        self.report_writer = ReportWriterAgent()
        self.reviewer = ReviewerAgent()

        # Initialize data storage
        self.data_storage = None
        if DATA_TOOLS_AVAILABLE:
            try:
                self.data_storage = get_data_storage(data_storage_dir)
                datasets_count = len(self.data_storage.index.get("items", {}))
                logger.info(f"Data storage initialized, {datasets_count} datasets available")
            except Exception as e:
                logger.warning(f"Data storage initialization failed: {e}")

        # Initialize knowledge graph
        self.knowledge_graph = None
        self.knowledge_graph_enabled = KNOWLEDGE_GRAPH_CONFIG.get("enabled", False) and KNOWLEDGE_GRAPH_AVAILABLE
        if self.knowledge_graph_enabled:
            try:
                kg_dir = knowledge_graph_dir or KNOWLEDGE_GRAPH_CONFIG.get("storage_dir", "data/methodology_graph")
                self.knowledge_graph = get_methodology_graph(storage_dir=kg_dir)
                node_count = len(self.knowledge_graph.nodes)
                edge_count = len(self.knowledge_graph.edges)
                logger.info(f"Knowledge graph initialized, {node_count} nodes, {edge_count} edges")
            except Exception as e:
                logger.warning(f"Knowledge graph initialization failed: {e}")
                self.knowledge_graph_enabled = False

        # Initialize report generator
        self.report_generator = ReportGenerator(str(output_dir))

        logger.info("Research orchestrator initialized")

    def run_full_pipeline(
        self,
        research_topic: str = None,
        user_input: str = None,
        keyword_group_a: List[str] = None,
        keyword_group_b: List[str] = None,
        min_papers: int = 10,
        data_info: Optional[str] = None,
        data_file: Optional[str] = None,
        word_count: int = 8000,
        enable_steps: Optional[List[str]] = None,
        enable_review: bool = True,
        enable_knowledge_graph: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Run the full research pipeline

        Pipeline: Complete research paper first -> then conduct reviewer assessment

        Args:
            research_topic: Research topic (can be None if user_input is provided)
            user_input: User's natural language input (e.g. "I want to study the effect of X on Y")
            keyword_group_a: Keyword group A (can be None if user_input is provided)
            keyword_group_b: Keyword group B (can be None if user_input is provided)
            min_papers: Minimum number of papers
            data_info: Data information (optional)
            data_file: Specified data file path (optional, data info will be auto-extracted if provided)
            word_count: Report word count
            enable_steps: List of enabled steps, runs all steps if None
                         Options: ["input_parse", "literature", "variable", "theory", "model", "analysis", "report"]
            enable_review: Whether to enable reviewer assessment (enabled by default, runs after paper completion)
            enable_knowledge_graph: Whether to enable knowledge graph for method recommendation (None uses default config)

        Returns:
            Dictionary containing all results
        """
        # If user_input is provided without research_topic, or input_parse step is explicitly enabled
        parsed_input = ""
        if (user_input and not research_topic) or (enable_steps and "input_parse" in enable_steps):
            if not user_input:
                raise ValueError("user_input must be provided when input_parse step is enabled")

            logger.info("=" * 50)
            logger.info("Step 0/7: Input Parsing")
            logger.info("=" * 50)

            input_result = self.input_parser.run({
                "user_input": user_input,
            })

            # Extract data from structured output
            parsed_data = input_result.get("parsed_data", {})
            parsed_input = input_result.get("parsed_input", "")

            # Extract information from parsed_data
            if not research_topic and parsed_data:
                research_topic = parsed_data.get("research_topic", user_input)

            # Extract variable info for subsequent steps
            variable_x = parsed_data.get("variable_x", {})
            variable_y = parsed_data.get("variable_y", {})
            keywords = parsed_data.get("keywords", {})

            # If keywords not provided, try to extract from parsed results
            if not keyword_group_a and keywords:
                keyword_group_a = keywords.get("group_a", {}).get("chinese", [])
            if not keyword_group_b and keywords:
                keyword_group_b = keywords.get("group_b", {}).get("chinese", [])

        if not research_topic:
            raise ValueError("Must provide research_topic or user_input")

        logger.info(f"Starting research pipeline: {research_topic}")

        # 显示可用数据集信息
        if self.data_storage:
            datasets_count = len(self.data_storage.index.get("items", {}))
            logger.info(f"可用数据集: {datasets_count} 个")

        # 默认启用所有步骤（除了input_parse，需要显式启用；review默认启用）
        if enable_steps is None:
            enable_steps = ["literature", "variable", "theory", "model", "analysis", "report"]

        results = {
            "research_topic": research_topic,
        }

        if user_input:
            results["user_input"] = user_input
            if parsed_input:
                results["parsed_input"] = parsed_input
            if 'parsed_data' in locals():
                results["input_parsed_data"] = parsed_data
            if 'variable_x' in locals():
                results["variable_x"] = variable_x
                results["variable_y"] = variable_y

        if keyword_group_a:
            results["keyword_group_a"] = keyword_group_a
        if keyword_group_b:
            results["keyword_group_b"] = keyword_group_b

        try:
            # ========== 阶段1: 论文撰写 ==========

            # 步骤1: 文献搜集
            if "literature" in enable_steps:
                logger.info("=" * 50)
                logger.info("步骤1/7: 文献搜集")
                logger.info("=" * 50)

                literature_result = self.literature_collector.run({
                    "research_topic": research_topic,
                    "keyword_group_a": keyword_group_a or [],
                    "keyword_group_b": keyword_group_b or [],
                    "min_papers": min_papers,
                })

                # 从结构化输出中提取数据
                parsed_data = literature_result.get("parsed_data", {})
                results["literature_summary"] = literature_result.get("literature_summary", "")
                results["literature_list"] = parsed_data.get("literature_list", [])

                # 保存阶段性结果
                self._save_stage_result(results, "1_literature")

            # 步骤2: 指标设置
            if "variable" in enable_steps:
                logger.info("=" * 50)
                logger.info("步骤2/7: 指标设置")
                logger.info("=" * 50)

                variable_input = {
                    "research_topic": research_topic,
                    "literature_summary": results.get("literature_summary", ""),
                }

                # 如果有解析后的输入，传递X和Y变量信息给variable_designer
                if "variable_x" in results:
                    variable_input["variable_x"] = results["variable_x"]
                if "variable_y" in results:
                    variable_input["variable_y"] = results["variable_y"]
                if "parsed_input" in results:
                    variable_input["parsed_input"] = results["parsed_input"]

                variable_result = self.variable_designer.run(variable_input)

                # 从结构化输出中提取数据
                parsed_data = variable_result.get("parsed_data", {})
                results["variable_system"] = variable_result.get("variable_system", "")
                results["variable_system_data"] = parsed_data

                # 保存阶段性结果
                self._save_stage_result(results, "2_variable")

            # 步骤3: 理论设置
            if "theory" in enable_steps:
                logger.info("=" * 50)
                logger.info("步骤3/7: 理论设置")
                logger.info("=" * 50)

                theory_result = self.theory_designer.run({
                    "research_topic": research_topic,
                    "variable_system": results.get("variable_system", ""),
                    "literature_summary": results.get("literature_summary", ""),
                })

                # 从结构化输出中提取数据
                parsed_data = theory_result.get("parsed_data", {})
                results["theory_framework"] = theory_result.get("theory_framework", "")
                results["theory_framework_data"] = parsed_data

                # 保存阶段性结果
                self._save_stage_result(results, "3_theory")

            # 步骤4: 计量模型设计
            if "model" in enable_steps:
                logger.info("=" * 50)
                logger.info("步骤4/7: 计量模型设计")
                logger.info("=" * 50)

                # 准备模型设计输入
                model_input = {
                    "research_topic": research_topic,
                    "variable_system": results.get("variable_system", ""),
                    "theory_framework": results.get("theory_framework", ""),
                }

                # 使用知识图谱推荐方法
                use_kg = enable_knowledge_graph if enable_knowledge_graph is not None else self.knowledge_graph_enabled
                if use_kg and self.knowledge_graph:
                    try:
                        # 从变量信息中提取X和Y
                        x_query = ""
                        y_query = ""
                        if "variable_x" in results:
                            x_query = results["variable_x"].get("name", "")
                        if "variable_y" in results:
                            y_query = results["variable_y"].get("name", "")

                        # 如果没有明确的X/Y，尝试从研究主题中提取
                        if not x_query or not y_query:
                            x_query = x_query or research_topic
                            y_query = y_query or research_topic

                        logger.info(f"使用知识图谱推荐方法 (X: {x_query}, Y: {y_query})")

                        # 获取方法推荐
                        kg_config = KNOWLEDGE_GRAPH_CONFIG if KNOWLEDGE_GRAPH_AVAILABLE else {}
                        recommendations = self.knowledge_graph.recommend_methods(
                            x_query, y_query,
                            top_k=kg_config.get("top_k", 5)
                        )

                        if recommendations:
                            # 格式化推荐结果
                            method_recommendations = []
                            for rec in recommendations:
                                method_recommendations.append(
                                    f"- {rec['method']} (使用频次: {rec['frequency']}次, 参考论文: {', '.join(rec['example_papers'][:2])})"
                                )
                            model_input["knowledge_graph_recommendations"] = "\n".join(method_recommendations)
                            results["kg_method_recommendations"] = recommendations
                            logger.info(f"知识图谱推荐了 {len(recommendations)} 个计量方法")
                        else:
                            logger.info("知识图谱未找到相关方法推荐")
                    except Exception as e:
                        logger.warning(f"知识图谱方法推荐失败: {e}")

                model_result = self.model_designer.run(model_input)

                # 从结构化输出中提取数据
                parsed_data = model_result.get("parsed_data", {})
                results["model_design"] = model_result.get("model_design", "")
                results["model_design_data"] = parsed_data
                results["knowledge_graph_enabled"] = use_kg and self.knowledge_graph is not None

                # 保存阶段性结果
                self._save_stage_result(results, "4_model")

            # 步骤5: 数据分析
            if "analysis" in enable_steps:
                logger.info("=" * 50)
                logger.info("步骤5/7: 数据分析")
                logger.info("=" * 50)

                analysis_input = {
                    "research_topic": research_topic,
                    "variable_system": results.get("variable_system", ""),
                    "theory_framework": results.get("theory_framework", ""),
                    "model_design": results.get("model_design", ""),
                    "data_info": data_info or "",
                }

                # 如果指定了数据文件，使用run_with_data
                if data_file:
                    logger.info(f"使用指定数据文件: {data_file}")
                    analysis_result = self.data_analyst.run_with_data(analysis_input, data_file)
                else:
                    # 自动搜索相关数据集
                    analysis_result = self.data_analyst.run(analysis_input)

                # 从结构化输出中提取数据
                parsed_data = analysis_result.get("parsed_data", {})
                results["data_analysis"] = analysis_result.get("data_analysis", "")
                results["data_analysis_data"] = parsed_data
                results["data_tools_available"] = analysis_result.get("data_tools_available", False)
                results["datasets_count"] = analysis_result.get("datasets_count", 0)

                # 保存阶段性结果
                self._save_stage_result(results, "5_analysis")

            # 步骤6: 长文报告撰写
            if "report" in enable_steps:
                logger.info("=" * 50)
                logger.info("步骤6/7: 长文报告撰写")
                logger.info("=" * 50)

                report_result = self.report_writer.run({
                    "research_topic": research_topic,
                    "literature_summary": results.get("literature_summary", ""),
                    "variable_system": results.get("variable_system", ""),
                    "theory_framework": results.get("theory_framework", ""),
                    "model_design": results.get("model_design", ""),
                    "data_analysis": results.get("data_analysis", ""),
                    "word_count": word_count,
                })
                results["final_report"] = report_result.get("final_report", "")

                # 保存阶段性结果
                self._save_stage_result(results, "6_report")

            # ========== 生成最终报告文件 ==========

            logger.info("=" * 50)
            logger.info("生成完整报告文件")
            logger.info("=" * 50)

            # 生成LaTeX格式论文
            latex_path = self.report_generator.generate_full_report(
                research_topic,
                results,
                format="latex"
            )
            results["latex_path"] = latex_path
            logger.info(f"LaTeX论文已生成: {latex_path}")

            # 生成Markdown格式备份（便于阅读）
            report_path = self.report_generator.generate_full_report(
                research_topic,
                results,
                format="markdown"
            )
            results["report_path"] = report_path
            logger.info(f"Markdown报告已生成: {report_path}")

            # 生成JSON格式备份（便于数据处理）
            json_path = self.report_generator.generate_full_report(
                research_topic,
                results,
                format="json"
            )
            results["json_path"] = json_path
            logger.info(f"JSON数据已生成: {json_path}")

            # ========== 阶段2: 审稿人评审 ==========

            # 步骤7: 审稿人评审（在论文完成后进行评分）
            if enable_review:
                logger.info("=" * 50)
                logger.info("步骤7/7: 审稿人评审（论文评分）")
                logger.info("=" * 50)

                review_result = self.reviewer.run({
                    "research_topic": research_topic,
                    "variable_system": results.get("variable_system", ""),
                    "theory_framework": results.get("theory_framework", ""),
                    "model_design": results.get("model_design", ""),
                    "data_analysis": results.get("data_analysis", ""),
                    "final_report": results.get("final_report", ""),
                })

                # 从结构化输出中提取数据
                parsed_data = review_result.get("parsed_data", {})
                results["review_report"] = review_result.get("review_report", "")
                results["review_report_data"] = parsed_data

                # 提取评分信息
                if parsed_data:
                    results["review_scores"] = {
                        "overall_score": parsed_data.get("overall_score"),
                        "dimension_scores": parsed_data.get("dimension_scores", {}),
                        "decision": parsed_data.get("decision"),
                    }
                    logger.info(f"LLM 论文评分: {parsed_data.get('overall_score', 'N/A')}")

                # 提取 AES 评分信息
                if review_result.get("aes_enabled", False):
                    results["aes_score"] = review_result.get("aes_score", {})
                    aes_normalized = results["aes_score"].get("normalized_score", 0)
                    logger.info(f"AES 自动评分: {aes_normalized:.2f}/100")

                # 保存阶段性结果
                self._save_stage_result(results, "7_review")

            logger.info("=" * 50)
            logger.info(f"研究流程完成！")
            logger.info("=" * 50)
            logger.info(f"生成的文件:")
            logger.info(f"  - LaTeX论文: {latex_path}")
            logger.info(f"  - Markdown报告: {report_path}")
            logger.info(f"  - JSON数据: {json_path}")
            if enable_review and "review_scores" in results:
                logger.info(f"评分结果:")
                logger.info(f"  - 论文评分: {results['review_scores'].get('overall_score', 'N/A')}")
                if "aes_score" in results:
                    aes_score = results["aes_score"]
                    logger.info(f"  - AES评分: {aes_score.get('normalized_score', 'N/A'):.2f}/100")
            logger.info("=" * 50)

            return results

        except Exception as e:
            logger.error(f"研究流程失败: {str(e)}")
            raise

    def run_single_step(
        self,
        step: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        运行单个步骤

        Args:
            step: 步骤名称 ("input_parse", "literature", "variable", "theory", "model", "analysis", "report", "review")
            input_data: 输入数据

        Returns:
            步骤结果
        """
        logger.info(f"运行单个步骤: {step}")

        if step == "input_parse":
            return self.input_parser.run(input_data)
        elif step == "literature":
            return self.literature_collector.run(input_data)
        elif step == "variable":
            return self.variable_designer.run(input_data)
        elif step == "theory":
            return self.theory_designer.run(input_data)
        elif step == "model":
            return self.model_designer.run(input_data)
        elif step == "analysis":
            return self.data_analyst.run(input_data)
        elif step == "report":
            return self.report_writer.run(input_data)
        elif step == "review":
            return self.reviewer.run(input_data)
        else:
            raise ValueError(f"未知的步骤: {step}")

    def search_datasets(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        搜索可用数据集

        Args:
            query: 搜索查询
            n_results: 返回结果数

        Returns:
            匹配的数据集列表
        """
        return self.data_analyst.search_data(query, n_results)

    def preview_dataset(self, file_path: str) -> Dict[str, Any]:
        """
        预览数据集

        Args:
            file_path: 数据文件路径

        Returns:
            数据预览信息
        """
        return self.data_analyst.preview_dataset(file_path)

    def _save_stage_result(self, results: Dict[str, Any], stage: str):
        """
        保存阶段性结果

        Args:
            results: 当前结果
            stage: 阶段名称
        """
        try:
            from datetime import datetime
            import json

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{stage}_{timestamp}.json"
            filepath = self.output_dir / "stages" / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            logger.info(f"阶段性结果已保存: {filepath}")

        except Exception as e:
            logger.warning(f"保存阶段性结果失败: {str(e)}")


class SimplifiedOrchestrator:
    """
    简化的编排器
    用于快速测试或简单场景
    """

    def __init__(
        self,
        data_storage_dir: str = "data/datasets",
        literature_storage_dir: str = "data/literature"
    ):
        self.orchestrator = ResearchOrchestrator(
            data_storage_dir=data_storage_dir,
            literature_storage_dir=literature_storage_dir
        )

    def quick_research(
        self,
        topic: str,
        keywords_a: str,
        keywords_b: str,
        data_file: Optional[str] = None,
        enable_review: bool = True,
    ) -> str:
        """
        快速研究（自动解析关键词）

        Args:
            topic: 研究主题
            keywords_a: 关键词组A（用逗号或顿号分隔）
            keywords_b: 关键词组B（用逗号或顿号分隔）
            data_file: 指定的数据文件路径（可选）
            enable_review: 是否启用审稿人评审

        Returns:
            报告路径
        """
        # 解析关键词
        import re
        keyword_group_a = re.split(r'[,，、]', keywords_a)
        keyword_group_b = re.split(r'[,，、]', keywords_b)

        keyword_group_a = [k.strip() for k in keyword_group_a if k.strip()]
        keyword_group_b = [k.strip() for k in keyword_group_b if k.strip()]

        results = self.orchestrator.run_full_pipeline(
            research_topic=topic,
            keyword_group_a=keyword_group_a,
            keyword_group_b=keyword_group_b,
            data_file=data_file,
            enable_review=enable_review,
        )

        return results.get("report_path", "")

    def search_data(self, query: str) -> List[Dict[str, Any]]:
        """搜索数据集"""
        return self.orchestrator.search_datasets(query)
