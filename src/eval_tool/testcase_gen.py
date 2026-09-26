"""
【模块定位】流程层 - 测试用例自动生成模块
【核心功能】输入需求文本，调用LLM自动生成测试用例草稿
【设计思想】测试左移，从需求阶段自动产出用例，减少人工编写成本
"""
from uuid import uuid4
import json

from .adapters.openai_adapter import call_openai_completion


def gen_testcases_from_requirement(
    req_text: str,
    n: int = 3,
    model_conf: dict | None = None
) -> list:
    """
    根据需求文本自动生成测试用例
    :param req_text: 需求描述文本
    :param n: 生成用例数量
    :param model_conf: 模型配置
    :return: 生成的用例列表
    """
    # 默认模型配置
    model_conf = model_conf or {
        "name": "gpt-3.5-turbo",
        "temperature": 0.0,
        "max_tokens": 1024
    }

    # 生成用例的Prompt
    prompt = f"""请根据以下需求生成 {n} 条测试用例，严格输出JSON数组格式，每条用例包含id、title、input、expected四个字段。

需求内容：
{req_text}

输出："""

    # 调用大模型生成
    resp = call_openai_completion(
        prompt,
        model=model_conf.get("name"),
        temperature=model_conf.get("temperature", 0.0),
        max_tokens=model_conf.get("max_tokens", 1024)
    )

    text = resp.get("text", "")

    try:
        # 尝试解析JSON
        parsed = text.strip()
        # 简单清理markdown代码块标记
        if parsed.startswith("```json"):
            parsed = parsed[7:-3].strip()
        if parsed.startswith("```"):
            parsed = parsed[3:-3].strip()

        out = json.loads(parsed)

        # 补全缺失的id
        for item in out:
            if not item.get("id"):
                item["id"] = uuid4().hex[:8]

        return out

    except Exception as e:
        # 解析失败返回原始文本，标记为待人工处理
        return [{
            "id": uuid4().hex[:8],
            "title": "自动生成失败-需人工处理",
            "input": "",
            "expected": text,
            "error": str(e)
        }]
