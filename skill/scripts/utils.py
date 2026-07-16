#!/usr/bin/env python3
"""
utils.py — AI知识图谱学习助手 通用工具模块

提供配置加载、LLM API调用、JSON持久化、日志记录等基础功能。
所有模块通过此文件统一访问LLM，便于后续切换API提供商或模型。
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:
    yaml = None

# OpenAI 延迟导入，仅在 LLMClient 实际使用时加载

# ============================================================
# 日志配置
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("knowledge_graph")


# ============================================================
# 配置管理
# ============================================================
class ConfigManager:
    """
    配置管理器，支持多级配置加载：
    1. 先加载 references/api_config.yaml（默认配置）
    2. 再用项目根目录 api_config.yaml 覆盖（用户本地配置）
    3. 环境变量优先（如 API_KEY, BASE_URL 等）
    """

    DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "references" / "api_config.yaml"
    LOCAL_CONFIG_PATH = Path.cwd() / "api_config.yaml"

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_defaults()
        if config_path:
            self._merge(Path(config_path))
        else:
            if self.LOCAL_CONFIG_PATH.exists():
                self._merge(self.LOCAL_CONFIG_PATH)
            elif self.DEFAULT_CONFIG_PATH.exists():
                self._merge(self.DEFAULT_CONFIG_PATH)
        self._apply_env_overrides()

    def _load_defaults(self) -> dict:
        return {
            "llm": {
                "provider": "openai-compatible",
                "api_key": "",
                "base_url": "https://api.deepseek.com/v1",
                "model": "deepseek-chat",
                "temperature": 0.3,
                "max_tokens": 4096,
            },
            "extraction": {
                "max_chunk_size": 8000,
                "overlap_size": 500,
            },
            "graph": {
                "max_nodes_per_graph": 200,
            },
            "output": {
                "format": "json",
                "indent": 2,
            },
        }

    def _merge(self, path: Path):
        if not path.exists():
            return
        user_config = {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                if yaml is not None:
                    user_config = yaml.safe_load(f) or {}
                else:
                    import json as _json
                    user_config = _json.load(f) or {}
        except Exception as e:
            logger.warning(f"加载配置文件失败: {path}, 原因: {e}")
            return
        self._deep_merge(self.config, user_config)
        logger.info(f"已加载配置文件: {path}")

    def _deep_merge(self, base: dict, override: dict):
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _apply_env_overrides(self):
        env_map = {
            "LLM_API_KEY": ("llm", "api_key"),
            "LLM_BASE_URL": ("llm", "base_url"),
            "LLM_MODEL": ("llm", "model"),
        }
        for env_var, (section, key) in env_map.items():
            if os.environ.get(env_var):
                self.config[section][key] = os.environ[env_var]
                logger.info(f"环境变量覆盖: {env_var} -> {section}.{key}")

    def get(self, *keys: str, default: Any = None) -> Any:
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value


# ============================================================
# LLM 客户端（单例模式）
# ============================================================
class LLMClient:
    """
    统一的LLM客户端封装。
    支持OpenAI兼容接口（DeepSeek / 豆包 / 通义千问等均可使用）。
    """

    _instance: Optional["LLMClient"] = None
    _config: Optional[ConfigManager] = None

    def __new__(cls, config: Optional[ConfigManager] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        if config and not cls._instance._initialized:
            cls._instance._init(config)
        return cls._instance

    def _init(self, config: ConfigManager):
        api_key = config.get("llm", "api_key", default="")
        base_url = config.get("llm", "base_url", default="https://api.deepseek.com/v1")

        if not api_key:
            logger.warning("API密钥未设置！请配置 api_config.yaml 或设置环境变量 LLM_API_KEY")

        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = config.get("llm", "model", default="deepseek-chat")
        self.temperature = config.get("llm", "temperature", default=0.3)
        self.max_tokens = config.get("llm", "max_tokens", default=4096)
        self._config = config
        self._initialized = True

    def chat(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """
        发送聊天请求，返回模型回复文本。

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户输入
            **kwargs: 覆盖默认参数（temperature, max_tokens等）

        Returns:
            模型回复的文本内容
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
            )
            content = response.choices[0].message.content
            logger.info(f"LLM调用成功，返回{len(content)}字符，消耗{response.usage.total_tokens} tokens")
            return content
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            raise

    def chat_json(self, system_prompt: str, user_prompt: str, **kwargs) -> dict:
        """
        发送聊天请求并解析JSON返回。

        Args:
            system_prompt: 系统提示词（需包含"返回JSON格式"的指令）
            user_prompt: 用户输入
            **kwargs: 覆盖默认参数

        Returns:
            解析后的JSON字典
        """
        raw = self.chat(system_prompt, user_prompt, **kwargs)
        return self._parse_json(raw)

    @staticmethod
    def _parse_json(raw: str) -> dict:
        """从LLM回复中提取JSON"""
        raw = raw.strip()
        # 尝试直接解析
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        # 尝试提取```json代码块
        if "```json" in raw:
            start = raw.find("```json") + 7
            end = raw.find("```", start)
            if end > start:
                return json.loads(raw[start:end].strip())
        if "```" in raw:
            start = raw.find("```") + 3
            end = raw.find("```", start)
            if end > start:
                return json.loads(raw[start:end].strip())
        raise ValueError(f"无法解析LLM返回的JSON: {raw[:200]}...")


# ============================================================
# 文件操作工具
# ============================================================
def load_text(file_path: str) -> str:
    """加载文本文件"""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def save_json(data: Any, file_path: str, indent: int = 2):
    """保存JSON文件，自动创建父目录"""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
    logger.info(f"已保存: {file_path}")


def load_json(file_path: str) -> Any:
    """加载JSON文件"""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def chunk_text(text: str, max_size: int = 8000, overlap: int = 500) -> list[str]:
    """
    将长文本分块，保持段落完整性。

    Args:
        text: 原始文本
        max_size: 每块最大字符数
        overlap: 块之间重叠字符数

    Returns:
        文本块列表
    """
    if len(text) <= max_size:
        return [text]

    chunks = []
    paragraphs = text.split("\n\n")
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_size:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            # 保留重叠部分
            if overlap > 0 and chunks:
                overlap_text = current[-overlap:] if len(current) > overlap else current
                current = overlap_text + "\n\n" + para
            else:
                current = para

    if current.strip():
        chunks.append(current)

    return chunks


# ============================================================
# 全局便捷函数
# ============================================================
_CONFIG: Optional[ConfigManager] = None
_LLM: Optional[LLMClient] = None


def init(config_path: Optional[str] = None):
    """初始化全局配置和LLM客户端"""
    global _CONFIG, _LLM
    _CONFIG = ConfigManager(config_path)
    _LLM = LLMClient(_CONFIG)
    return _CONFIG, _LLM


def get_config() -> ConfigManager:
    global _CONFIG
    if _CONFIG is None:
        init()
    return _CONFIG


def get_llm() -> LLMClient:
    global _LLM
    if _LLM is None:
        init()
    return _LLM
