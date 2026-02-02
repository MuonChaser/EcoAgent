"""
Configuration Management Module
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project root directory
ROOT_DIR = Path(__file__).parent.parent

# API Configuration - Aliyun DashScope support
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# OpenAI compatible configuration (for switching if needed)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

# Use Aliyun as default configuration
API_KEY = DASHSCOPE_API_KEY or OPENAI_API_KEY
API_BASE = DASHSCOPE_BASE_URL if DASHSCOPE_API_KEY else OPENAI_API_BASE

# Model configuration
DEFAULT_MODEL = "qwen-plus"
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# Directory configuration
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"
LOG_DIR = ROOT_DIR / "logs"

# Create necessary directories
for directory in [DATA_DIR, OUTPUT_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOG_DIR / "econometrics_agent.log"

# Agent configuration
AGENT_CONFIG = {
    "input_parser": {
        "name": "Input Parser",
        "model": DEFAULT_MODEL,
        "temperature": 0.3,  # Lower temperature for parsing accuracy
    },
    "literature_collector": {
        "name": "Literature Collector",
        "model": DEFAULT_MODEL,
        "temperature": 0.3,  # Lower temperature for accuracy
    },
    "variable_designer": {
        "name": "Variable Designer",
        "model": DEFAULT_MODEL,
        "temperature": 0.5,
    },
    "theory_designer": {
        "name": "Theory Designer",
        "model": DEFAULT_MODEL,
        "temperature": 0.6,
    },
    "model_designer": {
        "name": "Econometric Model Designer",
        "model": DEFAULT_MODEL,
        "temperature": 0.4,
    },
    "data_analyst": {
        "name": "Data Analyst",
        "model": DEFAULT_MODEL,
        "temperature": 0.3,
    },
    "report_writer": {
        "name": "Report Writer",
        "model": DEFAULT_MODEL,
        "temperature": 0.7,  # Higher temperature for creativity
    },
    "reviewer": {
        "name": "Reviewer",
        "model": DEFAULT_MODEL,
        "temperature": 0.4,  # Medium temperature for objectivity and flexibility
    },
    "literature_manager": {
        "name": "Literature Manager",
        "model": DEFAULT_MODEL,
        "temperature": 0.3,  # Low temperature for parsing accuracy
    },
}

# Literature storage configuration
LITERATURE_STORAGE_CONFIG = {
    "storage_dir": str(DATA_DIR / "literature"),
    "collection_name": "research_literature",
    "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2",
}

# Data storage configuration (for storing dataset summaries and paths)
DATA_STORAGE_CONFIG = {
    "storage_dir": str(DATA_DIR / "datasets"),
    "collection_name": "research_datasets",
    "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2",
}

# Raw data directory
RAW_DATA_DIR = DATA_DIR / "raw"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Literature search configuration
LITERATURE_CONFIG = {
    "min_papers": 10,
    "max_papers": 20,
    "years_range": 10,
    "top_journals": [
        "AER", "JPE", "QJE", "Econometrica", "Review of Economic Studies",
        "Journal of Finance", "Review of Financial Studies", "Journal of Financial Economics", "Management Science"
    ]
}

# Variable configuration
VARIABLE_CONFIG = {
    "min_proxy_variables_x": 3,
    "min_proxy_variables_y": 1,
    "min_control_variables": 5,
}

# Model selection configuration
MODEL_CONFIG = {
    "base_models": ["OLS", "Fixed Effects", "DID", "IV", "RDD", "PSM"],
    "robustness_checks": 3,
}

# Knowledge graph configuration
KNOWLEDGE_GRAPH_CONFIG = {
    "enabled": os.getenv("ENABLE_KNOWLEDGE_GRAPH", "true").lower() == "true",  # Whether to enable knowledge graph
    "storage_dir": str(DATA_DIR / "methodology_graph"),  # Storage directory
    "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2",  # Embedding model
    "top_k": 5,  # Number of similar nodes to retrieve
    "k_hops": 1,  # Neighborhood expansion hops
    "similarity_threshold": 0.3,  # Similarity threshold
}

# LangChain Callbacks configuration
ENABLE_TRACING = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "econometrics-research")
LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
