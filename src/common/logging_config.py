"""
所有服务的日志配置
"""

import logging.config
import sys
from pathlib import Path
from typing import Any, Dict

from .config import settings


def get_logging_config() -> Dict[str, Any]:
    """
    返回日志配置字典。

    此配置提供：
    - 开发环境中的彩色控制台输出
    - 生产环境中的文件输出
    - 结构化 JSON 日志选项
    """
    log_level = settings.log_level.upper()

    # 确保文件日志的日志目录存在
    if settings.environment == "production":
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(module)s %(funcName)s %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "default"
                if settings.environment == "development"
                else "json",
                "stream": sys.stdout,
            },
        },
        "loggers": {
            "": {  # 根日志记录器
                "level": log_level,
                "handlers": ["console"],
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": "WARNING" if not settings.debug else "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "celery": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }

    # 为生产环境添加文件处理器
    if settings.environment == "production":
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "detailed",
            "filename": "logs/agent_studio.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        }

        # 将文件处理器添加到所有日志记录器
        for logger in config["loggers"].values():
            logger["handlers"].append("file")

    return config


def setup_logging():
    """为应用程序配置日志"""
    logging_config = get_logging_config()
    logging.config.dictConfig(logging_config)

    # 获取根日志记录器
    logger = logging.getLogger(__name__)
    logger.info(f"日志配置环境: {settings.environment}")
    logger.info(f"日志级别: {settings.log_level}")

    return logger
