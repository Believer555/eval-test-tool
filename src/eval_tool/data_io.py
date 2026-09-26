"""
【模块定位】数据层 - 数据导入导出模块
【核心功能】读取JSONL/CSV格式数据集，转换为内部TestCase实体入库
【设计思想】统一数据入口，支持行业标准JSONL格式，数据与代码分离
"""
import json
import csv
from pathlib import Path
from typing import List, Dict
from uuid import uuid4

from .db import TestCase, SessionLocal


def read_jsonl(path: str) -> List[Dict]:
    """
    读取JSONL格式文件
    JSONL：每行一条独立JSON数据，适合增量追加、版本管理
    :param path: 文件路径
    :return: 字典列表
    """
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # 跳过空行
            if not line:
                continue
            # 解析单行JSON并加入列表
            out.append(json.loads(line))
    return out


def import_dataset_jsonl(path: str, dataset_name: str) -> int:
    """
    将JSONL数据集导入为TestCase并入库
    :param path: JSONL文件路径
    :param dataset_name: 数据集名称，用于生成标题前缀
    :return: 成功导入的数量
    """
    # 读取原始数据
    items = read_jsonl(path)
    saved = 0

    # 创建数据库会话
    session = SessionLocal()

    try:
        for it in items:
            # 优先使用数据中的id，没有则自动生成8位UUID
            tc_id = it.get("id") or f"{dataset_name}-{uuid4().hex[:8]}"

            # 创建TestCase实例
            tc = TestCase(
                id=tc_id,
                title=f"{dataset_name}::{tc_id}",
                # input和expected统一序列化为JSON字符串存储，兼容各种类型
                input=json.dumps(it.get("input"), ensure_ascii=False),
                expected=json.dumps(it.get("reference"), ensure_ascii=False),
            )

            # merge语义：存在则更新，不存在则新增
            # 优势：重复导入不会产生重复数据
            session.merge(tc)
            saved += 1

        # 提交事务
        session.commit()
    except Exception:
        # 异常回滚
        session.rollback()
        raise
    finally:
        # 关闭会话
        session.close()

    return saved
