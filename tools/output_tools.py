"""
工具模块 - 输出格式化工具
"""
from typing import Dict, Any, List
import json
from pathlib import Path
from datetime import datetime
from loguru import logger


class OutputFormatter:
    """
    输出格式化工具
    """
    
    @staticmethod
    def format_to_markdown(content: Dict[str, Any], title: str = "研究报告") -> str:
        """
        将内容格式化为Markdown
        
        Args:
            content: 内容字典
            title: 标题
            
        Returns:
            Markdown格式文本
        """
        lines = [
            f"# {title}",
            "",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            ""
        ]
        
        for key, value in content.items():
            lines.append(f"## {key}")
            lines.append("")
            
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    lines.append(f"### {sub_key}")
                    lines.append("")
                    lines.append(str(sub_value))
                    lines.append("")
            else:
                lines.append(str(value))
                lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_to_latex(content: str, title: str = "研究报告") -> str:
        """
        将内容格式化为LaTeX文档
        
        Args:
            content: 内容字符串
            title: 标题
            
        Returns:
            LaTeX格式文本
        """
        latex_template = r"""
\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage{ctex}
\usepackage{amsmath}
\usepackage{booktabs}
\usepackage{graphicx}
\usepackage{hyperref}

\title{TITLE}
\date{\today}

\begin{document}

\maketitle

CONTENT

\end{document}
"""
        
        latex_doc = latex_template.replace("TITLE", title).replace("CONTENT", content)
        return latex_doc
    
    @staticmethod
    def save_to_file(content: str, filepath: str, format: str = "txt") -> bool:
        """
        保存内容到文件
        
        Args:
            content: 内容
            filepath: 文件路径
            format: 格式 ("txt", "md", "tex", "json")
            
        Returns:
            是否成功
        """
        try:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            if format == "json":
                if isinstance(content, str):
                    content = {"content": content}
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(content, f, ensure_ascii=False, indent=2)
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            logger.info(f"内容已保存到: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"保存文件失败: {str(e)}")
            return False
    
    @staticmethod
    def create_table(data: List[List[Any]], headers: List[str] = None) -> str:
        """
        创建Markdown表格
        
        Args:
            data: 表格数据
            headers: 表头
            
        Returns:
            Markdown表格文本
        """
        if not data:
            return ""
        
        lines = []
        
        # 添加表头
        if headers:
            lines.append("| " + " | ".join(str(h) for h in headers) + " |")
            lines.append("| " + " | ".join("---" for _ in headers) + " |")
        
        # 添加数据行
        for row in data:
            lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
        
        return "\n".join(lines)


class ReportGenerator:
    """
    报告生成器
    """
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_full_report(
        self,
        research_topic: str,
        results: Dict[str, Any],
        format: str = "markdown"
    ) -> str:
        """
        生成完整研究报告

        Args:
            research_topic: 研究主题
            results: 各阶段结果
            format: 输出格式 ("markdown", "json", "latex")

        Returns:
            报告文件路径
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 构建报告内容
            content = {
                "研究主题": research_topic,
                "文献综述": results.get("literature_summary", ""),
                "变量体系": results.get("variable_system", ""),
                "理论框架": results.get("theory_framework", ""),
                "模型设计": results.get("model_design", ""),
                "数据分析": results.get("data_analysis", ""),
                "完整报告": results.get("final_report", ""),
            }

            if format == "latex":
                # 首先尝试从 final_report 的 latex_source 字段提取 LaTeX
                latex_content = None
                final_report = results.get("final_report", "")

                # 如果 final_report 是字符串（可能是JSON），尝试解析
                if isinstance(final_report, str):
                    try:
                        # 移除可能的 markdown 代码块标记
                        import json
                        clean_json = final_report.strip()
                        if clean_json.startswith("```json"):
                            clean_json = clean_json[7:]
                        if clean_json.endswith("```"):
                            clean_json = clean_json[:-3]

                        # 尝试解析 JSON
                        report_data = json.loads(clean_json.strip())
                        latex_content = report_data.get("latex_source")
                    except Exception as e:
                        # 不是 JSON，检查是否直接是 LaTeX
                        if "\\documentclass" in final_report:
                            latex_content = final_report
                elif isinstance(final_report, dict):
                    # 如果已经是字典，直接取 latex_source
                    latex_content = final_report.get("latex_source")

                # 检查是否成功获取 LaTeX 内容
                if latex_content and "\\documentclass" in latex_content:
                    filepath = self.output_dir / f"paper_{timestamp}.tex"
                    OutputFormatter.save_to_file(latex_content, str(filepath), "tex")
                    logger.info(f"LaTeX论文已保存: {filepath}")
                else:
                    logger.warning("final_report 不包含 LaTeX 内容（latex_source 字段为空或无效），回退到 markdown 格式")
                    formatted = OutputFormatter.format_to_markdown(content, research_topic)
                    filepath = self.output_dir / f"report_{timestamp}.md"
                    OutputFormatter.save_to_file(formatted, str(filepath), "md")
            elif format == "markdown":
                formatted = OutputFormatter.format_to_markdown(content, research_topic)
                filepath = self.output_dir / f"report_{timestamp}.md"
                OutputFormatter.save_to_file(formatted, str(filepath), "md")
            elif format == "json":
                filepath = self.output_dir / f"report_{timestamp}.json"
                OutputFormatter.save_to_file(content, str(filepath), "json")
            else:
                formatted = json.dumps(content, ensure_ascii=False, indent=2)
                filepath = self.output_dir / f"report_{timestamp}.txt"
                OutputFormatter.save_to_file(formatted, str(filepath), "txt")

            logger.info(f"完整报告已生成: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"生成报告失败: {str(e)}")
            return ""
    
    def generate_summary(self, results: Dict[str, Any]) -> str:
        """
        生成研究摘要
        
        Args:
            results: 研究结果
            
        Returns:
            摘要文本
        """
        summary_parts = []
        
        if "research_topic" in results:
            summary_parts.append(f"研究主题: {results['research_topic']}")
        
        if "literature_summary" in results:
            summary_parts.append("\n文献综述已完成")
        
        if "variable_system" in results:
            summary_parts.append("变量体系已设计")
        
        if "theory_framework" in results:
            summary_parts.append("理论框架已构建")
        
        if "model_design" in results:
            summary_parts.append("计量模型已设计")
        
        if "data_analysis" in results:
            summary_parts.append("数据分析已完成")
        
        if "final_report" in results:
            summary_parts.append("完整报告已撰写")
        
        return "\n".join(summary_parts)
