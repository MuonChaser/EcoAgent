"""
研究流程的多层记忆系统
提供智能上下文共享，避免 token 浪费
"""

from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from loguru import logger
from datetime import datetime


class ResearchMemory:
    """
    研究流程的三层记忆系统（简化实现）

    架构:
    1. Summary Store - 全局摘要（压缩所有历史）
    2. Buffer Store - 最近缓存（保留最近 N 个 agent 的完整输出）
    3. Structured Store - 结构化存储（保存关键数据）
    """

    def __init__(self, llm: Optional[ChatOpenAI] = None, buffer_size: int = 2):
        """
        初始化记忆系统

        Args:
            llm: 用于生成摘要的 LLM（可选，暂时不使用）
            buffer_size: 缓存中保留的最近交互数量
        """
        self.llm = llm
        self.buffer_size = buffer_size

        # 1. 全局摘要存储（存储每个 agent 的简要摘要）
        self.summary_store: List[str] = []

        # 2. 最近阶段缓存（保留最近 N 个 agent 的完整输出）
        self.buffer_store: List[Dict[str, Any]] = []

        # 3. 结构化数据存储（保存关键研究要素）
        self.structured_store: Dict[str, Any] = {
            "research_topic": None,
            "variable_system": None,
            "theory_framework": None,
            "model_design": None,
            "data_analysis": None,
        }

        # Agent 执行历史
        self.agent_history: List[Dict[str, Any]] = []

        logger.info(f"ResearchMemory 初始化完成 (buffer_size={buffer_size})")

    def add_agent_output(self, agent_name: str, output: Dict[str, Any]):
        """
        添加 agent 输出到记忆系统

        Args:
            agent_name: Agent 名称
            output: Agent 输出数据
        """
        # 1. 记录到历史
        self.agent_history.append({
            "agent_name": agent_name,
            "output": output,
            "timestamp": self._get_timestamp()
        })

        # 2. 生成摘要并保存到 summary store
        summary = self._generate_summary(agent_name, output)
        self.summary_store.append(summary)

        # 3. 保存完整输出到 buffer store（保持固定大小）
        self.buffer_store.append({
            "agent_name": agent_name,
            "output": output,
            "timestamp": self._get_timestamp()
        })

        # 如果超过 buffer_size，移除最旧的记录
        if len(self.buffer_store) > self.buffer_size:
            self.buffer_store.pop(0)

        # 4. 更新结构化存储
        self._update_structured_store(agent_name, output)

        logger.info(f"[Memory] {agent_name} 输出已保存到记忆系统")

    def get_context_for_agent(self, agent_name: str) -> str:
        """
        为特定 agent 获取相关上下文

        Args:
            agent_name: Agent 名称

        Returns:
            格式化的上下文字符串
        """
        context_parts = []

        # 1. 添加全局摘要
        if self.summary_store:
            context_parts.append("# 研究历史摘要")
            # 只显示最近5个摘要以避免过长
            recent_summaries = self.summary_store[-5:]
            for summary in recent_summaries:
                context_parts.append(summary)
            context_parts.append("")

        # 2. 添加最近上下文（来自 buffer store）
        if self.buffer_store:
            context_parts.append("# 最近阶段输出")
            for buffer_item in self.buffer_store:
                agent = buffer_item["agent_name"]
                output = buffer_item["output"]
                parsed_data = output.get("parsed_data", {})

                # 格式化输出
                context_parts.append(f"## {agent}")
                # 限制长度
                output_str = str(parsed_data)
                if len(output_str) > 300:
                    output_str = output_str[:300] + "..."
                context_parts.append(output_str)

            context_parts.append("")

        # 3. 根据 agent 需求添加特定结构化数据
        if agent_name in ["report_writer", "reviewer"] and self.structured_store:
            context_parts.append("# 关键研究要素")
            for key, value in self.structured_store.items():
                if value is not None:
                    context_parts.append(f"## {key}")
                    # 限制每个字段的长度以避免过长
                    value_str = str(value)
                    if len(value_str) > 500:
                        value_str = value_str[:500] + "..."
                    context_parts.append(value_str)
                    context_parts.append("")

        return "\n".join(context_parts)

    def _generate_summary(self, agent_name: str, output: Dict[str, Any]) -> str:
        """
        生成输出摘要

        Args:
            agent_name: Agent 名称
            output: Agent 输出数据

        Returns:
            摘要文本
        """
        parsed = output.get("parsed_data", {})

        if isinstance(parsed, dict) and parsed:
            summary_parts = [f"{agent_name} 完成："]

            # 提取前 3 个关键字段
            key_fields = list(parsed.keys())[:3]
            for key in key_fields:
                value = parsed[key]
                # 截取前 100 个字符
                value_str = str(value)[:100]
                if len(str(value)) > 100:
                    value_str += "..."
                summary_parts.append(f"- {key}: {value_str}")

            return "\n".join(summary_parts)
        else:
            # 如果不是字典，直接返回长度信息
            return f"{agent_name} 完成，输出长度: {len(str(parsed))} 字符"

    def _update_structured_store(self, agent_name: str, output: Dict[str, Any]):
        """
        更新结构化存储

        Args:
            agent_name: Agent 名称
            output: Agent 输出数据
        """
        parsed = output.get("parsed_data", {})

        # Agent 到结构化存储的映射
        store_mapping = {
            "input_parser": "research_topic",
            "variable_designer": "variable_system",
            "theory_designer": "theory_framework",
            "model_designer": "model_design",
            "data_analyst": "data_analysis",
        }

        # 如果有映射，更新存储
        if agent_name in store_mapping:
            store_key = store_mapping[agent_name]

            # 对于 input_parser，特殊处理
            if agent_name == "input_parser":
                self.structured_store[store_key] = parsed.get("research_topic")
            else:
                self.structured_store[store_key] = parsed

            logger.debug(f"[Memory] 更新结构化存储: {store_key}")

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_summary(self) -> str:
        """
        获取完整的研究流程摘要

        Returns:
            研究流程摘要文本
        """
        summary_parts = ["# 研究流程总结\n"]

        # 1. 基本信息
        if self.structured_store["research_topic"]:
            summary_parts.append(f"**研究主题**: {self.structured_store['research_topic']}\n")

        # 2. Agent 执行历史
        summary_parts.append(f"**执行步骤**: {len(self.agent_history)} 个阶段\n")
        for i, history_item in enumerate(self.agent_history, 1):
            agent_name = history_item["agent_name"]
            timestamp = history_item["timestamp"]
            summary_parts.append(f"{i}. {agent_name} ({timestamp})")

        # 3. 关键研究要素
        summary_parts.append("\n## 关键研究要素\n")
        for key, value in self.structured_store.items():
            if value is not None:
                summary_parts.append(f"- **{key}**: 已完成")

        return "\n".join(summary_parts)

    def clear(self):
        """清空记忆系统"""
        self.summary_store = []
        self.buffer_store = []
        self.structured_store = {k: None for k in self.structured_store}
        self.agent_history = []
        logger.info("[Memory] 记忆系统已清空")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取记忆系统统计信息

        Returns:
            统计信息字典
        """
        return {
            "agent_history_count": len(self.agent_history),
            "summary_store_count": len(self.summary_store),
            "buffer_store_count": len(self.buffer_store),
            "buffer_size": self.buffer_size,
            "structured_store_keys": list(self.structured_store.keys()),
            "structured_store_completed": sum(1 for v in self.structured_store.values() if v is not None),
        }
