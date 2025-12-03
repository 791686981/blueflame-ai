"""
使用 Pydantic BaseSettings 进行配置管理
"""

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """从环境变量加载的应用程序设置"""

    # ========== 基础配置 ==========

    # postgreSQL 数据库连接 URL（env: DATABASE_URL）
    postgres_uri: str = Field(
        default="postgresql://postgres:postgres@49.233.19.26:5432/enn_agent_studio?sslmode=disable",
        env="DATABASE_URL",
        description="PostgreSQL 数据库连接 URL",
    )

    # # Redis 配置（暂时注释）
    # redis_url: str = Field(
    #     default="redis://localhost:6379/0",
    #     env="REDIS_URL",
    #     description="Redis 连接 URL，用于 Celery 和缓存",
    # )

    # 内部 API 密钥（env: INTERNAL_API_KEY）
    internal_api_key: str = Field(
        default="dev-api-key",
        env="INTERNAL_API_KEY",
        description="内部服务通信的密钥",
    )

    # FastAPI / JWT 配置（当前 .env 未提供，先注释）
    # secret_key: str = Field(default="dev-secret-key-change-in-production", env="SECRET_KEY", description="JWT 密钥")
    # algorithm: str = Field(default="HS256", env="ALGORITHM", description="JWT 算法")
    # access_token_expire_minutes: int = Field(
    #     default=30,
    #     env="ACCESS_TOKEN_EXPIRE_MINUTES",
    #     description="JWT 令牌过期时间（分钟）",
    # )

    # # 代理服务器配置（暂时注释）
    # agent_server_host: str = Field(
    #     default="localhost", env="AGENT_SERVER_HOST", description="代理服务器主机"
    # )

    # agent_server_port: int = Field(
    #     default=8001, env="AGENT_SERVER_PORT", description="代理服务器端口"
    # )

    # # Celery 配置（暂时注释）
    # celery_broker_url: str = Field(
    #     default="redis://localhost:6379/0",
    #     env="CELERY_BROKER_URL",
    #     description="Celery 消息代理 URL",
    # )

    # celery_result_backend: str = Field(
    #     default="redis://localhost:6379/0",
    #     env="CELERY_RESULT_BACKEND",
    #     description="Celery 结果后端 URL",
    # )

    # 环境
    environment: str = Field(
        default="development",
        env="ENVIRONMENT",
        description="应用程序环境（开发/生产）",
    )

    debug: bool = Field(default=False, env="DEBUG", description="调试模式")

    # CORS 配置
    backend_cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="BACKEND_CORS_ORIGINS",
        description="允许的 CORS 源",
    )

    # 日志级别
    log_level: str = Field(default="INFO", env="LOG_LEVEL", description="日志级别")

    # ========== LLM 配置 ==========

    # Siliconflow 配置
    siliconflow_api_key: str = Field(
        default="", env="SILICONFLOW_API_KEY", description="Siliconflow API 密钥"
    )

    # DashScope 配置
    dashscope_api_key: str = Field(
        default="", env="DASHSCOPE_API_KEY", description="DashScope API 密钥"
    )

    # 火山引擎 Ark 配置
    ark_api_key: str = Field(
        default="", env="ARK_API_KEY", description="火山引擎 Ark API 密钥"
    )

    # ========== LangSmith 配置 ==========

    langsmith_api_key: str = Field(
        default="", env="LANGSMITH_API_KEY", description="LangSmith API 密钥"
    )

    # ========== 工具 API 配置 ==========

    # Unstructured 配置
    unstructured_api_key: str = Field(
        default="", env="UNSTRUCTURED_API_KEY", description="Unstructured API 密钥"
    )

    # Firecrawl 配置
    firecrawl_api_key: str = Field(
        default="", env="Firecrawl_API_KEY", description="Firecrawl API 密钥"
    )

    # Tavily 搜索配置
    tavily_api_key: str = Field(
        default="", env="TAVILY_API_KEY", description="Tavily 搜索 API 密钥"
    )

    # 高德地图 API 配置
    amap_maps_api_key: str = Field(
        default="", env="AMAP_MAPS_API_KEY", description="高德地图 API 密钥"
    )

    # ========== LLM 模型配置 ==========

    # LLM 模型默认值（当前 .env 未提供，先注释）
    # default_llm_model: str = Field(
    #     default="deepseek_v3",
    #     env="DEFAULT_LLM_MODEL",
    #     description="默认使用的LLM模型名称"
    # )

    # OpenAI API（当前 .env 未提供，先注释）
    # openai_api_key: str = Field(
    #     default="",
    #     env="OPENAI_API_KEY",
    #     description="OpenAI API 密钥"
    # )
    # openai_api_base: str = Field(
    #     default="https://api.openai.com/v1",
    #     env="OPENAI_API_BASE",
    #     description="OpenAI API 基础URL"
    # )

    # @property
    # def agent_server_url(self) -> str:
    #     """获取完整的代理服务器 URL"""
    #     return f"http://{self.agent_server_host}:{self.agent_server_port}"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # 允许额外的字段


# 创建全局设置实例
settings = Settings()
