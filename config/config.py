"""
配置管理模块
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent

# API配置 - 支持阿里云通义千问
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# 兼容OpenAI配置（如果需要切换）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

# 使用阿里云作为默认配置
API_KEY = DASHSCOPE_API_KEY or OPENAI_API_KEY
API_BASE = DASHSCOPE_BASE_URL if DASHSCOPE_API_KEY else OPENAI_API_BASE

# 模型配置
DEFAULT_MODEL = "qwen-plus"
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# 目录配置
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"
LOG_DIR = ROOT_DIR / "logs"

# 创建必要的目录
for directory in [DATA_DIR, OUTPUT_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOG_DIR / "econometrics_agent.log"

# 智能体配置
AGENT_CONFIG = {
    "input_parser": {
        "name": "输入解析专家",
        "model": DEFAULT_MODEL,
        "temperature": 0.3,  # 较低温度保证解析准确性
    },
    "literature_collector": {
        "name": "文献搜集专家",
        "model": DEFAULT_MODEL,
        "temperature": 0.3,  # 较低温度保证准确性
    },
    "variable_designer": {
        "name": "指标设置专家",
        "model": DEFAULT_MODEL,
        "temperature": 0.5,
    },
    "theory_designer": {
        "name": "理论设置专家",
        "model": DEFAULT_MODEL,
        "temperature": 0.6,
    },
    "model_designer": {
        "name": "计量模型专家",
        "model": DEFAULT_MODEL,
        "temperature": 0.4,
    },
    "data_analyst": {
        "name": "数据分析专家",
        "model": DEFAULT_MODEL,
        "temperature": 0.3,
    },
    "report_writer": {
        "name": "长文报告专家",
        "model": DEFAULT_MODEL,
        "temperature": 0.7,  # 较高温度增加创造性
    },
    "reviewer": {
        "name": "审稿人专家",
        "model": DEFAULT_MODEL,
        "temperature": 0.4,  # 中等温度，保证评审的客观性和灵活性
    },
    "literature_manager": {
        "name": "文献管理专家",
        "model": DEFAULT_MODEL,
        "temperature": 0.3,  # 低温度确保解析准确性
    },
}

# 文献存储配置
LITERATURE_STORAGE_CONFIG = {
    "storage_dir": str(DATA_DIR / "literature"),
    "collection_name": "research_literature",
    "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2",
}

# 数据存储配置 (用于存储数据集摘要和路径)
DATA_STORAGE_CONFIG = {
    "storage_dir": str(DATA_DIR / "datasets"),
    "collection_name": "research_datasets",
    "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2",
}

# 原始数据目录
RAW_DATA_DIR = DATA_DIR / "raw"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

# 文献搜索配置
LITERATURE_CONFIG = {
    "min_papers": 10,
    "max_papers": 20,
    "years_range": 10,
    "top_journals": [
        "AER", "JPE", "QJE", "Econometrica", "Review of Economic Studies",
        "经济研究", "经济学（季刊）", "管理世界", "中国工业经济"
    ]
}

# 变量配置
VARIABLE_CONFIG = {
    "min_proxy_variables_x": 3,
    "min_proxy_variables_y": 1,
    "min_control_variables": 5,
}

# 模型配置
MODEL_CONFIG = {
    "base_models": ["OLS", "Fixed Effects", "DID", "IV", "RDD", "PSM"],
    "robustness_checks": 3,
}

# LangChain Callbacks 配置
ENABLE_TRACING = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "econometrics-research")
LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
