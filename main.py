"""
主入口文件
"""
# ⚠️ 必须在所有其他导入之前加载环境变量！
from dotenv import load_dotenv
load_dotenv()

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger
from config.logging_config import setup_logger

# 配置日志
LOG_FILE = setup_logger("main")

from orchestrator import ResearchOrchestrator, SimplifiedOrchestrator

__version__ = "1.1.0"

__all__ = [
    "ResearchOrchestrator",
    "SimplifiedOrchestrator",
]
