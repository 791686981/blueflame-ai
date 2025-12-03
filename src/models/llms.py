"""
通用LLM模型加载器
"""

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from ..common.config import settings

logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    """支持的模型提供商枚举"""

    OPENAI = "openai"
    SILICONFLOW = "siliconflow"
    DASHSCOPE = "dashscope"
    VOLCENGINE = "volcengine"


class ModelConfig:
    """模型配置类"""

    def __init__(
        self,
        provider: ModelProvider,
        model_name: str,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        max_retries: int = 3,
        timeout: int = 120,
        **kwargs,
    ):
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key
        self.api_base = api_base
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.timeout = timeout
        self.extra_kwargs = kwargs


class BaseModelLoader(ABC):
    """抽象模型加载器基类"""

    @abstractmethod
    def load_model(self, config: ModelConfig) -> BaseChatModel:
        """加载模型的抽象方法"""
        pass


class OpenAILoader(BaseModelLoader):
    """OpenAI模型加载器"""

    def load_model(self, config: ModelConfig) -> ChatOpenAI:
        """加载OpenAI兼容的模型"""
        return ChatOpenAI(
            api_key=config.api_key,
            model=config.model_name,
            base_url=config.api_base,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            max_retries=config.max_retries,
            timeout=config.timeout,
            **config.extra_kwargs,
        )

class ModelFactory:
    """模型工厂类"""

    _loaders: Dict[ModelProvider, BaseModelLoader] = {
        ModelProvider.OPENAI: OpenAILoader(),
        ModelProvider.SILICONFLOW: OpenAILoader(),
        ModelProvider.VOLCENGINE: OpenAILoader(),
    }

    @classmethod
    def create_model(cls, config: ModelConfig) -> BaseChatModel:
        """创建模型实例"""
        loader = cls._loaders.get(config.provider)
        if not loader:
            raise ValueError(f"不支持的模型提供商: {config.provider}")

        logger.info(f"正在加载模型: {config.provider.value} - {config.model_name}")
        return loader.load_model(config)

    @classmethod
    def register_loader(cls, provider: ModelProvider, loader: BaseModelLoader):
        """注册新的模型加载器"""
        cls._loaders[provider] = loader


class LLMManager:
    """LLM模型管理器"""

    def __init__(self):
        self._models: Dict[str, BaseChatModel] = {}
        self._configs: Dict[str, ModelConfig] = {}

    def register_model(self, name: str, config: ModelConfig, lazy_load: bool = True):
        """注册模型配置"""
        self._configs[name] = config
        if not lazy_load:
            self._models[name] = ModelFactory.create_model(config)
            logger.info(f"模型 {name} 已预加载")

    def get_model(self, name: str) -> BaseChatModel:
        """获取模型实例"""
        if name not in self._models:
            if name not in self._configs:
                raise ValueError(f"未找到模型配置: {name}")

            config = self._configs[name]
            self._models[name] = ModelFactory.create_model(config)
            logger.info(f"模型 {name} 已加载")

        return self._models[name]

    def list_models(self) -> Dict[str, ModelConfig]:
        """列出所有已注册的模型配置"""
        return self._configs.copy()


# 全局LLM管理器实例
llm_manager = LLMManager()

# 常用模型配置
PREDEFINED_MODELS = {
    # SiliconFlow-DeepSeek V3
    "DeepSeek-V3.1": ModelConfig(
        provider=ModelProvider.SILICONFLOW,
        model_name="deepseek-ai/DeepSeek-V3.1-Terminus",
        api_key=settings.siliconflow_api_key,
        api_base="https://api.siliconflow.cn/v1",
        temperature=0,
        max_tokens=160000,
    ),
    # Volcengine Ark - Doubao（OpenAI兼容）
    # 参考 curl: https://ark.cn-beijing.volces.com/api/v3/chat/completions
    "doubao-seed-1-6": ModelConfig(
        provider=ModelProvider.VOLCENGINE,
        model_name="doubao-seed-1-6-251015",
        api_key=settings.ark_api_key,
        api_base="https://ark.cn-beijing.volces.com/api/v3",
        temperature=0,
        max_tokens=256000,
        timeout=120,
        # Ark 参数兼容：通过 extra_body 传自定义字段
        extra_body={"max_completion_tokens": 2048, "reasoning_effort": "medium"},
    ),
    # SiliconFlow-DeepSeek V3.2
    "DeepSeek-V3.2": ModelConfig(
        provider=ModelProvider.SILICONFLOW,
        model_name="deepseek-ai/DeepSeek-V3.2-Exp",
        api_key=settings.siliconflow_api_key,
        api_base="https://api.siliconflow.cn/v1",
        temperature=0,
        max_tokens=160000,
    ),
    # SiliconFlow-Kimi-K2-Thinking
    "Kimi-K2-Thinking": ModelConfig(
        provider=ModelProvider.SILICONFLOW,
        model_name="moonshotai/Kimi-K2-Thinking",
        api_key=settings.siliconflow_api_key,
        api_base="https://api.siliconflow.cn/v1",
        temperature=0,
        max_tokens=256000,
    ),
    # SiliconFlow - MiniMax M2
    "MiniMax-M2": ModelConfig(
        provider=ModelProvider.SILICONFLOW,
        model_name="MiniMaxAI/MiniMax-M2",
        api_key=settings.siliconflow_api_key,
        api_base="https://api.siliconflow.cn/v1",
        temperature=0,
        max_tokens=200000,
    ),
    # SiliconFlow - GLM 4.6
    "GLM-4.6": ModelConfig(
        provider=ModelProvider.SILICONFLOW,
        model_name="zai-org/GLM-4.6",
        api_key=settings.siliconflow_api_key,
        api_base="https://api.siliconflow.cn/v1",
        temperature=0,
        max_tokens=200000,
    ),
    # SiliconFlow - Qwen3-VL-235B A22B Instruct
    "Qwen3-VL-235B-A22B-Instruct": ModelConfig(
        provider=ModelProvider.SILICONFLOW,
        model_name="Qwen/Qwen3-VL-235B-A22B-Instruct",
        api_key=settings.siliconflow_api_key,
        api_base="https://api.siliconflow.cn/v1",
        temperature=0,
        max_tokens=256000,
    ),
    # SiliconFlow - Qwen3-VL-235B A22B Thinking
    "Qwen3-VL-235B-A22B-Thinking": ModelConfig(
        provider=ModelProvider.SILICONFLOW,
        model_name="Qwen/Qwen3-VL-235B-A22B-Thinking",
        api_key=settings.siliconflow_api_key,
        api_base="https://api.siliconflow.cn/v1",
        temperature=0,
        max_tokens=256000,
    ),
    # SiliconFlow - DeepSeek OCR
    "DeepSeek-OCR": ModelConfig(
        provider=ModelProvider.SILICONFLOW,
        model_name="deepseek-ai/DeepSeek-OCR",
        api_key=settings.siliconflow_api_key,
        api_base="https://api.siliconflow.cn/v1",
        temperature=0,
        max_tokens=8000,
    ),
    # SiliconFlow - GLM 4.5V
    "GLM-4.5V": ModelConfig(
        provider=ModelProvider.SILICONFLOW,
        model_name="zai-org/GLM-4.5V",
        api_key=settings.siliconflow_api_key,
        api_base="https://api.siliconflow.cn/v1",
        temperature=0,
        max_tokens=64000,
    ),
    # SiliconFlow - GLM 4.5-Air
    "GLM-4.5-Air": ModelConfig(
        provider=ModelProvider.SILICONFLOW,
        model_name="zai-org/GLM-4.5-Air",
        api_key=settings.siliconflow_api_key,
        api_base="https://api.siliconflow.cn/v1",
        temperature=0,
        max_tokens=128000,
    ),
    # 默认模型
    "default": ModelConfig(
        provider=ModelProvider.SILICONFLOW,
        model_name="deepseek-ai/DeepSeek-V3.1-Terminus",
        api_key=settings.siliconflow_api_key,
        api_base="https://api.siliconflow.cn/v1",
        temperature=0,
        max_retries=5,
        timeout=120,
    ),
}

# 自动注册预定义模型
for model_name, config in PREDEFINED_MODELS.items():
    llm_manager.register_model(model_name, config)


# 便捷函数
def get_llm(model_name: str = "default") -> BaseChatModel:
    """获取LLM模型的便捷函数"""
    return llm_manager.get_model(model_name)


def register_custom_model(name: str, config: ModelConfig, lazy_load: bool = True):
    """注册自定义模型的便捷函数"""
    llm_manager.register_model(name, config, lazy_load)


# 向后兼容的全局变量
model = get_llm("default")


# ============ 使用示例 ============
"""
# 基本用法 - 使用预定义模型
from agent_service.agents.design_assistant.llms import get_llm

# 获取默认模型 (DeepSeek V3)
llm = get_llm()
llm = get_llm("default")

# 获取其他预定义模型
qwen_llm = get_llm("qwen2.5_72b")
claude_llm = get_llm("claude_3.5_sonnet")

# 注册和使用自定义模型
from agent_service.agents.design_assistant.llms import register_custom_model, ModelConfig, ModelProvider

custom_config = ModelConfig(
    provider=ModelProvider.SILICONFLOW,
    model_name="meta-llama/Llama-3.1-8B-Instruct",
    api_key="your_api_key",
    temperature=0.7,
    max_tokens=2048
)
register_custom_model("llama3.1_8b", custom_config)
llama_llm = get_llm("llama3.1_8b")

# 在Agent中使用
class MyAgent:
    def __init__(self, model_name: str = "default"):
        self.llm = get_llm(model_name)

    def process(self, text: str):
        response = self.llm.invoke(text)
        return response.content
"""


if __name__ == "__main__":
    # 简单的命令行入口：列出/查看/调用模型
    import argparse
    from pprint import pprint

    from langchain_core.messages import HumanMessage

    parser = argparse.ArgumentParser(description="LLM 预置模型工具")
    subparsers = parser.add_subparsers(dest="command", required=False)

    # list
    subparsers.add_parser("list", help="列出所有模型")

    # info
    p_info = subparsers.add_parser("info", help="查看单个模型详情")
    p_info.add_argument("name", help="模型名称")

    # run
    p_run = subparsers.add_parser("run", help="对指定模型发起一次简单对话")
    p_run.add_argument("name", help="模型名称")
    p_run.add_argument("prompt", help="用户输入提示词")

    # run-image（多模态：图片URL + 文本）
    p_run_img = subparsers.add_parser(
        "run-image", help="对指定模型发起一次图文对话（需要多模态支持）"
    )
    p_run_img.add_argument("name", help="模型名称")
    p_run_img.add_argument("image_url", help="图片URL")
    p_run_img.add_argument("prompt", help="文本提示词")

    args = parser.parse_args()
    cmd = args.command or "list"

    if cmd == "list":
        print("已注册模型（键名 → provider / model_name / max_tokens）：")
        for k, cfg in llm_manager.list_models().items():
            print(f"- {k} → {cfg.provider.value} / {cfg.model_name} / {cfg.max_tokens}")
    elif cmd == "info":
        cfg = llm_manager.list_models().get(args.name)
        if not cfg:
            parser.error(f"未找到模型：{args.name}")
        data = {
            "provider": cfg.provider.value,
            "model_name": cfg.model_name,
            "api_base": cfg.api_base,
            "temperature": cfg.temperature,
            "max_tokens": cfg.max_tokens,
            "max_retries": cfg.max_retries,
            "timeout": cfg.timeout,
            "extra": cfg.extra_kwargs,
        }
        pprint(data)
    elif cmd == "run":
        llm = get_llm(args.name)
        try:
            resp = llm.invoke(args.prompt)
            content = getattr(resp, "content", None)
            if isinstance(content, list):
                text_parts = [
                    p.get("text")
                    for p in content
                    if isinstance(p, dict) and p.get("type") == "text"
                ]
                print("".join([t for t in text_parts if t]))
            else:
                print(content or str(resp))
        except Exception as e:
            print(f"调用失败：{e}")
    elif cmd == "run-image":
        # 通过 LangChain HumanMessage 构造图文内容，兼容 Ark/SiliconFlow 的多模态格式
        llm = get_llm(args.name)
        content = [
            {"type": "image_url", "image_url": {"url": args.image_url}},
            {"type": "text", "text": args.prompt},
        ]
        try:
            resp = llm.invoke([HumanMessage(content=content)])
            content = getattr(resp, "content", None)
            if isinstance(content, list):
                text_parts = [
                    p.get("text")
                    for p in content
                    if isinstance(p, dict) and p.get("type") == "text"
                ]
                print("".join([t for t in text_parts if t]))
            else:
                print(content or str(resp))
        except Exception as e:
            print(f"调用失败：{e}")
    else:
        parser.error(f"未知命令：{cmd}")
