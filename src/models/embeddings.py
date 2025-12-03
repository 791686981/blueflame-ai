"""
通用Embedding模型加载器
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Optional

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
try:
    # 优先使用官方社区集成的 DashScopeEmbeddings
    from langchain_community.embeddings import DashScopeEmbeddings  # type: ignore
except Exception:  # pragma: no cover - 可选依赖
    DashScopeEmbeddings = None  # type: ignore

from ..common.config import settings

logger = logging.getLogger(__name__)


class EmbeddingProvider(str, Enum):
    """支持的Embedding提供商"""

    OPENAI = "openai"
    SILICONFLOW = "siliconflow"
    DASHSCOPE = "dashscope"


class EmbeddingModelConfig:
    """Embedding模型配置"""

    def __init__(
        self,
        provider: EmbeddingProvider,
        model_name: str,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        dimensions: Optional[int] = None,
        max_retries: int = 3,
        timeout: Optional[float] = 120,
        **kwargs,
    ):
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key
        self.api_base = api_base
        self.dimensions = dimensions
        self.max_retries = max_retries
        self.timeout = timeout
        self.extra_kwargs = kwargs


class BaseEmbeddingLoader(ABC):
    """抽象Embedding加载器"""

    @abstractmethod
    def load(self, config: EmbeddingModelConfig) -> Embeddings:
        """加载Embedding模型实例"""
        raise NotImplementedError


class OpenAIEmbeddingLoader(BaseEmbeddingLoader):
    """OpenAI兼容的Embedding加载器（适用于SiliconFlow等）"""

    def load(self, config: EmbeddingModelConfig) -> Embeddings:
        kwargs = dict(
            model=config.model_name,
            api_key=config.api_key,
            base_url=config.api_base,
            max_retries=config.max_retries,
        )
        # dimensions为可选参数；若模型固定维度，可按需传入
        if config.dimensions:
            kwargs["dimensions"] = config.dimensions
        # OpenAIEmbeddings支持timeout参数（httpx超时），按需传入
        if config.timeout is not None:
            kwargs["timeout"] = config.timeout

        # 透传额外参数
        kwargs.update(config.extra_kwargs)

        return OpenAIEmbeddings(**kwargs)


class DashScopeEmbeddingLoader(BaseEmbeddingLoader):
    """阿里云百炼 DashScope 原生 Embeddings 加载器。

    依赖 `langchain-community` 包提供的 `DashScopeEmbeddings` 集成。
    """

    def load(self, config: EmbeddingModelConfig) -> Embeddings:  # type: ignore[override]
        if DashScopeEmbeddings is None:
            raise ImportError(
                "未安装 langchain-community，无法使用 DashScopeEmbeddings。"
            )
        # DashScopeEmbeddings 接口：model + dashscope_api_key
        # base_url 由 SDK 内部处理；若未来支持自定义地域可在此扩展。
        return DashScopeEmbeddings(
            model=config.model_name,
            dashscope_api_key=config.api_key,
        )


class EmbeddingFactory:
    """Embedding工厂"""

    _loaders: Dict[EmbeddingProvider, BaseEmbeddingLoader] = {
        EmbeddingProvider.OPENAI: OpenAIEmbeddingLoader(),
        EmbeddingProvider.SILICONFLOW: OpenAIEmbeddingLoader(),
        EmbeddingProvider.DASHSCOPE: DashScopeEmbeddingLoader(),
    }

    @classmethod
    def create(cls, config: EmbeddingModelConfig) -> Embeddings:
        loader = cls._loaders.get(config.provider)
        if not loader:
            raise ValueError(f"不支持的Embedding提供商: {config.provider}")
        logger.info(
            f"正在加载Embedding模型: {config.provider.value} - {config.model_name}"
        )
        return loader.load(config)

    @classmethod
    def register_loader(cls, provider: EmbeddingProvider, loader: BaseEmbeddingLoader):
        cls._loaders[provider] = loader


class EmbeddingManager:
    """Embedding模型管理器"""

    def __init__(self):
        self._models: Dict[str, Embeddings] = {}
        self._configs: Dict[str, EmbeddingModelConfig] = {}

    def register(self, name: str, config: EmbeddingModelConfig, lazy_load: bool = True):
        self._configs[name] = config
        if not lazy_load:
            self._models[name] = EmbeddingFactory.create(config)
            logger.info(f"Embedding模型 {name} 已预加载")

    def get(self, name: str) -> Embeddings:
        if name not in self._models:
            if name not in self._configs:
                raise ValueError(f"未找到Embedding模型配置: {name}")
            config = self._configs[name]
            self._models[name] = EmbeddingFactory.create(config)
            logger.info(f"Embedding模型 {name} 已加载")
        return self._models[name]

    def list_configs(self) -> Dict[str, EmbeddingModelConfig]:
        return self._configs.copy()


# 全局Embedding管理器
embedding_manager = EmbeddingManager()


# 统一的 SiliconFlow 根地址（OpenAI兼容接口）
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
"""
说明：DashScope 原生集成使用 DashScopeEmbeddings 与官方 SDK 交互，
无需通过 OpenAI 兼容端点，因此未使用 `DASHSCOPE_BASE_URL`。
"""


# 预置Embedding模型（均为硅基流动）
PREDEFINED_EMBEDDINGS: Dict[str, EmbeddingModelConfig] = {
    # DashScope - text-embedding-v4（Qwen3-Embedding 系列，默认1024维，支持2048/1536/768/512/256/128/64）
    "text-embedding-v4": EmbeddingModelConfig(
        provider=EmbeddingProvider.DASHSCOPE,
        model_name="text-embedding-v4",
        api_key=settings.dashscope_api_key,
        dimensions=1024,
        max_retries=5,
        timeout=120,
    ),
    # Qwen3-Embedding-8B（4096维，32K）
    "Qwen3-Embedding-8B": EmbeddingModelConfig(
        provider=EmbeddingProvider.SILICONFLOW,
        model_name="Qwen/Qwen3-Embedding-8B",
        api_key=settings.siliconflow_api_key,
        api_base=SILICONFLOW_BASE_URL,
        dimensions=4096,
        max_retries=5,
        timeout=120,
    ),
    # BAAI bge-m3（1024维，8K）
    "bge-m3": EmbeddingModelConfig(
        provider=EmbeddingProvider.SILICONFLOW,
        model_name="Pro/BAAI/bge-m3",
        api_key=settings.siliconflow_api_key,
        api_base=SILICONFLOW_BASE_URL,
        dimensions=1024,
        max_retries=5,
        timeout=120,
    ),
    # 默认（设置为阿里云 DashScope 的 text-embedding-v4）
    "default": EmbeddingModelConfig(
        provider=EmbeddingProvider.DASHSCOPE,
        model_name="text-embedding-v4",
        api_key=settings.dashscope_api_key,
        dimensions=1024,
        max_retries=5,
        timeout=120,
    ),
}


# 注册预置模型
for name, cfg in PREDEFINED_EMBEDDINGS.items():
    embedding_manager.register(name, cfg)


# 便捷函数
def get_embedding_model(name: str = "default") -> Embeddings:
    return embedding_manager.get(name)


def register_custom_embedding(
    name: str, config: EmbeddingModelConfig, lazy_load: bool = True
):
    embedding_manager.register(name, config, lazy_load)


if __name__ == "__main__":
    # 简易命令行：列出或测试嵌入
    import argparse
    from pprint import pprint

    parser = argparse.ArgumentParser(description="Embedding 预置模型查看/测试工具")
    subparsers = parser.add_subparsers(dest="command", required=False)

    # list
    subparsers.add_parser("list", help="列出所有Embedding模型")

    # info
    p_info = subparsers.add_parser("info", help="查看单个模型配置")
    p_info.add_argument("name", help="模型名称")

    # run (对输入文本做一次embed)
    p_run = subparsers.add_parser("run", help="对文本进行一次嵌入计算")
    p_run.add_argument("name", help="模型名称")
    p_run.add_argument("text", help="要嵌入的文本")

    args = parser.parse_args()
    cmd = args.command or "list"

    if cmd == "list":
        print("已注册的Embedding模型（键名 → provider / model_name / dimensions）：")
        for k, cfg in embedding_manager.list_configs().items():
            print(f"- {k} → {cfg.provider.value} / {cfg.model_name} / {cfg.dimensions}")
    elif cmd == "info":
        cfg = embedding_manager.list_configs().get(args.name)
        if not cfg:
            parser.error(f"未找到模型：{args.name}")
        data = {
            "provider": cfg.provider.value,
            "model_name": cfg.model_name,
            "api_base": cfg.api_base,
            "dimensions": cfg.dimensions,
            "max_retries": cfg.max_retries,
            "timeout": cfg.timeout,
            "extra": cfg.extra_kwargs,
        }
        pprint(data)
    elif cmd == "run":
        model = embedding_manager.get(args.name)
        vec = model.embed_query(args.text)
        print(f"向量维度: {len(vec)}，前10个维度: {vec[:10]}")
    else:
        parser.error(f"未知命令：{cmd}")
