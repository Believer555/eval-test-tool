"""
【模块定位】能力层 - Prompt模板引擎
【核心功能】基于Jinja2实现Prompt模板化渲染，支持变量注入、长度控制
【设计思想】Prompt与代码分离，统一管理、版本化，保证评测输入一致性
"""
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

# 计算模板根目录：从当前文件往上一级，定位到templates目录
TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"

# 初始化Jinja2模板环境
env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape([]),  # 文本模板关闭自动转义
    trim_blocks=True,
    lstrip_blocks=True
)


def render_template(name: str, context: dict, max_length: int | None = None) -> str:
    """
    渲染指定模板
    :param name: 模板名称（相对于templates目录的路径）
    :param context: 模板变量字典
    :param max_length: 可选，最大长度限制，超过则截断
    :return: 渲染后的完整Prompt
    """
    # 加载模板文件
    tpl = env.get_template(name)
    # 渲染模板，传入变量
    out = tpl.render(**context)

    # 长度截断控制
    if max_length and len(out) > max_length:
        # 简单截断策略，可扩展为智能截断（保留结尾/保留开头）
        out = out[-max_length:]

    return out
