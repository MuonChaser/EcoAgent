"""
统一的日志配置模块

每次运行生成独立的日志文件，文件名包含脚本名和时间戳。

使用方法:
    from config.logging_config import setup_logger

    # 在脚本开头调用
    setup_logger("my_script")  # 生成 logs/my_script_20240129_143052.log

    # 或者自动使用调用者的脚本名
    setup_logger()  # 自动检测脚本名
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from loguru import logger

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 日志目录
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def setup_logger(
    script_name: str = None,
    level: str = "INFO",
    file_level: str = "DEBUG",
    console: bool = True
) -> Path:
    """
    配置日志系统，每次运行生成独立的日志文件

    Args:
        script_name: 脚本名称，用于日志文件命名。如果为 None，自动检测
        level: 控制台日志级别
        file_level: 文件日志级别
        console: 是否输出到控制台

    Returns:
        日志文件路径
    """
    # 自动检测脚本名
    if script_name is None:
        # 获取调用者的脚本名
        import inspect
        frame = inspect.stack()[1]
        caller_file = frame.filename
        script_name = Path(caller_file).stem

    # 生成带时间戳的日志文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"{script_name}_{timestamp}.log"

    # 移除默认处理器
    logger.remove()

    # 添加控制台处理器
    if console:
        logger.add(
            sys.stderr,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
            level=level
        )

    # 添加文件处理器
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level=file_level,
        encoding="utf-8",
        rotation=None,  # 不轮转，每次运行一个新文件
    )

    logger.info(f"日志文件: {log_file}")

    return log_file


def get_logger():
    """获取 logger 实例"""
    return logger


# 便捷变量
LOG_FILE = None  # 会在 setup_logger 调用后设置


def setup_logger_with_return(script_name: str = None, **kwargs) -> tuple:
    """
    配置日志并返回 logger 和日志文件路径

    Returns:
        (logger, log_file_path)
    """
    log_file = setup_logger(script_name, **kwargs)
    return logger, log_file
