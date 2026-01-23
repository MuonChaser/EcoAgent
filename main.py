"""
主入口文件
"""
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
