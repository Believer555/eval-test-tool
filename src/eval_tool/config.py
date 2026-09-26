"""
【模块定位】支撑层 - 全局配置管理模块
【核心功能】读取YAML配置文件，支持环境变量覆盖，对外提供统一的配置字典
【设计思想】配置与代码完全分离，所有可变参数集中管理
"""
import os
import yaml

# 计算默认配置文件路径：从当前文件往上两级，定位到configs/default.yaml
# 优势：无论脚本在哪个目录执行，都能准确定位配置文件
DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "configs",
    "default.yaml"
)


def load_config(path: str | None = None) -> dict:
    """
    加载配置文件
    :param path: 可选，指定配置文件路径，不传则使用默认路径
    :return: 配置字典
    """
    # 未指定路径则使用默认配置
    cfg_path = path or DEFAULT_CONFIG_PATH

    # 读取并解析YAML文件
    with open(cfg_path, "r", encoding="utf-8") as f:
        # safe_load安全解析，避免执行任意代码
        cfg = yaml.safe_load(f) or {}

    # 此处可扩展：用环境变量覆盖敏感配置项
    # 例如 os.environ.get("OPENAI_API_KEY") 优先级高于配置文件

    return cfg
