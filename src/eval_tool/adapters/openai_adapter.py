"""
【模块定位】适配层 - OpenAI模型适配器
【核心功能】封装OpenAI SDK调用，对外提供统一的调用接口与返回结构
【设计模式】适配器模式，所有模型适配器遵循相同的接口契约
【接口契约】统一返回 {text, latency_ms, tokens, raw} 结构
"""
import os
import time
import openai

# 从环境变量读取API密钥
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY


def call_openai_completion(
    prompt: str,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.0,
    max_tokens: int = 512,
    timeout: int = 30
) -> dict:
    """
    调用OpenAI对话补全接口
    :param prompt: 用户输入提示
    :param model: 模型名称
    :param temperature: 采样温度
    :param max_tokens: 最大生成token数
    :param timeout: 超时时间（秒）
    :return: 统一格式的结果字典
    """
    start = time.time()

    try:
        # 调用ChatCompletion接口（v1.x SDK写法）
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
    except Exception as e:
        # 异常统一封装，保证返回结构一致
        return {
            "text": "",
            "raw": str(e),
            "latency_ms": int((time.time() - start) * 1000),
            "tokens": None
        }

    # 提取回答文本
    text = ""
    if "choices" in resp and len(resp["choices"]) > 0:
        text = resp["choices"][0]["message"]["content"]

    # 计算耗时
    latency_ms = int((time.time() - start) * 1000)

    # 提取token使用量
    tokens = None
    usage = resp.get("usage", {})
    if usage:
        tokens = usage.get("total_tokens")

    return {
        "text": text,
        "raw": resp,
        "latency_ms": latency_ms,
        "tokens": tokens
    }
