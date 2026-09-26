"""
【模块定位】评测层 - 多维度指标引擎
【核心功能】三级评测指标：精确匹配→文本相似度→语义相似度
【设计思想】不同场景适配不同指标，不用单一标准衡量所有输出
"""
import json
import difflib
from typing import Dict

# 全局embedding模型变量，懒加载
_embed_model = None


def _ensure_embedding_model(model_name: str = "all-mpnet-base-v2"):
    """
    懒加载语义编码模型
    优势：不用不加载，节省启动时间和内存
    """
    global _embed_model
    if _embed_model is None:
        from sentence_transformers import SentenceTransformer
        _embed_model = SentenceTransformer(model_name)
    return _embed_model


def exact_match(expected: str, actual: str) -> bool:
    """
    精确匹配：规范化后完全相等
    最严格，适合事实类、指令类问题
    """
    try:
        # 统一去空格、转小写，消除格式差异
        a = (expected or "").strip().lower()
        b = (actual or "").strip().lower()
        return a == b
    except Exception:
        return False


def ratio_score(expected: str, actual: str) -> float:
    """
    文本相似度：基于difflib序列匹配
    衡量字面重合度，0~1，越高越相似
    """
    a = expected or ""
    b = actual or ""
    return difflib.SequenceMatcher(None, a, b).ratio()


def embedding_score(expected: str, actual: str, model_name: str = "all-mpnet-base-v2") -> float:
    """
    语义相似度：向量编码 + 余弦相似度
    衡量语义一致性，最接近人类判断
    """
    model = _ensure_embedding_model(model_name)
    from sentence_transformers import util

    # 编码为向量
    emb1 = model.encode(expected, convert_to_tensor=True)
    emb2 = model.encode(actual, convert_to_tensor=True)
    # 计算余弦相似度
    sim = util.pytorch_cos_sim(emb1, emb2).item()
    return float(sim)


def evaluate_single(expected: str, actual: str, use_embedding: bool = False) -> Dict:
    """
    对单条结果执行全量评测
    :param expected: 预期输出
    :param actual: 实际输出
    :param use_embedding: 是否计算语义相似度
    :return: 指标字典
    """
    # 处理预期值：如果是JSON字符串先尝试解析
    try:
        if expected and expected.strip().startswith(("{", "[")):
            exp_obj = json.loads(expected)
            exp_text = exp_obj if isinstance(exp_obj, str) else str(exp_obj)
        else:
            exp_text = expected or ""
    except Exception:
        exp_text = expected or ""

    act_text = actual or ""

    # 计算各项指标
    em = exact_match(exp_text, act_text)
    ratio = ratio_score(exp_text, act_text)

    # 语义相似度按需计算
    embed = None
    if use_embedding:
        embed = embedding_score(exp_text, act_text)

    return {
        "exact_match": em,      # 精确匹配布尔值
        "ratio": ratio,        # 文本相似度0~1
        "embedding": embed     # 语义相似度，未开启则为None
    }
