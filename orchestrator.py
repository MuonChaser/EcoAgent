"""
主协调器 - 编排和管理多个智能体的工作流程
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


class ResearchOrchestrator:
    """
    研究编排器
    负责协调各个智能体完成完整的研究流程
    """
    
    def __init__(self, output_dir: str = "output"):
        """
        初始化编排器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化所有智能体
        self.input_parser = InputParserAgent()
        self.literature_collector = LiteratureCollectorAgent()
        self.variable_designer = VariableDesignerAgent()
        self.theory_designer = TheoryDesignerAgent()
        self.model_designer = ModelDesignerAgent()
        self.data_analyst = DataAnalystAgent()
        self.report_writer = ReportWriterAgent()
        self.reviewer = ReviewerAgent()
        
        # 初始化报告生成器
        self.report_generator = ReportGenerator(str(output_dir))
        
        logger.info("研究编排器初始化完成")
    
    def run_full_pipeline(
        self,
        research_topic: str = None,
        user_input: str = None,
        keyword_group_a: List[str] = None,
        keyword_group_b: List[str] = None,
        min_papers: int = 10,
        data_info: Optional[str] = None,
        word_count: int = 8000,
        enable_steps: Optional[List[str]] = None,
        enable_review: bool = False,
    ) -> Dict[str, Any]:
        """
        运行完整的研究流程
        
        Args:
            research_topic: 研究主题（如果提供了user_input，可以为None）
            user_input: 用户的自然语言输入（如"我想研究X对Y的影响"）
            keyword_group_a: 关键词组A（如果提供了user_input，可以为None）
            keyword_group_b: 关键词组B（如果提供了user_input，可以为None）
            min_papers: 最少文献数量
            data_info: 数据信息（可选）
            word_count: 报告字数
            enable_steps: 启用的步骤列表，如果为None则运行所有步骤
                         可选值: ["input_parse", "literature", "variable", "theory", "model", "analysis", "report", "review"]
            enable_review: 是否启用审稿人评审
        
        Returns:
            包含所有结果的字典
        """
        # 如果提供了user_input但没有research_topic，或者显式启用input_parse步骤
        parsed_input = ""
        if (user_input and not research_topic) or (enable_steps and "input_parse" in enable_steps):
            if not user_input:
                raise ValueError("启用input_parse步骤时必须提供user_input")
            
            logger.info("=" * 50)
            logger.info("步骤0/7: 输入解析")
            logger.info("=" * 50)
            
            input_result = self.input_parser.run({
                "user_input": user_input,
            })
            
            # 从结构化输出中提取数据
            parsed_data = input_result.get("parsed_data", {})
            parsed_input = input_result.get("parsed_input", "")
            
            # 从parsed_data中提取信息
            if not research_topic and parsed_data:
                research_topic = parsed_data.get("research_topic", user_input)
            
            # 提取变量信息用于后续步骤
            variable_x = parsed_data.get("variable_x", {})
            variable_y = parsed_data.get("variable_y", {})
            keywords = parsed_data.get("keywords", {})
            
            # 如果没有提供关键词，尝试从解析结果中获取
            if not keyword_group_a and keywords:
                keyword_group_a = keywords.get("group_a", {}).get("chinese", [])
            if not keyword_group_b and keywords:
                keyword_group_b = keywords.get("group_b", {}).get("chinese", [])
        
        if not research_topic:
            raise ValueError("必须提供research_topic或user_input")
        
        logger.info(f"开始研究流程: {research_topic}")
        
        # 默认启用所有步骤（除了input_parse和review，需要显式启用）
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
                
                model_result = self.model_designer.run({
                    "research_topic": research_topic,
                    "variable_system": results.get("variable_system", ""),
                    "theory_framework": results.get("theory_framework", ""),
                })
                
                # 从结构化输出中提取数据
                parsed_data = model_result.get("parsed_data", {})
                results["model_design"] = model_result.get("model_design", "")
                results["model_design_data"] = parsed_data
                
                # 保存阶段性结果
                self._save_stage_result(results, "4_model")
            
            # 步骤5: 数据分析
            if "analysis" in enable_steps:
                logger.info("=" * 50)
                logger.info("步骤5/7: 数据分析")
                logger.info("=" * 50)
                
                analysis_result = self.data_analyst.run({
                    "research_topic": research_topic,
                    "variable_system": results.get("variable_system", ""),
                    "theory_framework": results.get("theory_framework", ""),
                    "model_design": results.get("model_design", ""),
                    "data_info": data_info or "请说明需要什么样的数据",
                })
                
                # 从结构化输出中提取数据
                parsed_data = analysis_result.get("parsed_data", {})
                results["data_analysis"] = analysis_result.get("data_analysis", "")
                results["data_analysis_data"] = parsed_data
                
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
            
            # 步骤7: 审稿人评审（可选）
            if enable_review or "review" in enable_steps:
                logger.info("=" * 50)
                logger.info("步骤7/7: 审稿人评审")
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
                
                # 保存阶段性结果
                self._save_stage_result(results, "7_review")
            
            # 生成最终完整报告
            logger.info("=" * 50)
            logger.info("生成完整报告")
            logger.info("=" * 50)

            # 生成LaTeX格式论文
            latex_path = self.report_generator.generate_full_report(
                research_topic,
                results,
                format="latex"
            )
            results["latex_path"] = latex_path

            # 生成Markdown格式备份（便于阅读）
            report_path = self.report_generator.generate_full_report(
                research_topic,
                results,
                format="markdown"
            )
            results["report_path"] = report_path

            # 生成JSON格式备份（便于数据处理）
            json_path = self.report_generator.generate_full_report(
                research_topic,
                results,
                format="json"
            )
            results["json_path"] = json_path
            
            logger.info("=" * 50)
            logger.info(f"研究流程完成！")
            logger.info(f"LaTeX论文: {latex_path}")
            logger.info(f"Markdown报告: {report_path}")
            logger.info(f"JSON数据: {json_path}")
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
    
    def __init__(self):
        self.orchestrator = ResearchOrchestrator()
    
    def quick_research(
        self,
        topic: str,
        keywords_a: str,
        keywords_b: str,
    ) -> str:
        """
        快速研究（自动解析关键词）
        
        Args:
            topic: 研究主题
            keywords_a: 关键词组A（用逗号或顿号分隔）
            keywords_b: 关键词组B（用逗号或顿号分隔）
        
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
        )
        
        return results.get("report_path", "")
