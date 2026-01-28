"""
主入口文件
"""
# ⚠️ 必须在所有其他导入之前加载环境变量！
from dotenv import load_dotenv
load_dotenv()

from loguru import logger
import sys
from pathlib import Path

# 配置日志
from config.config import LOG_FILE, LOG_LEVEL

logger.remove()
logger.add(sys.stderr, level=LOG_LEVEL)
logger.add(LOG_FILE, rotation="10 MB", level=LOG_LEVEL)

from orchestrator import ResearchOrchestrator, SimplifiedOrchestrator

__version__ = "1.1.0"

__all__ = [
    "ResearchOrchestrator",
    "SimplifiedOrchestrator",
]
