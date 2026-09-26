"""
【模块定位】流程层 - 缺陷跟踪模块
【核心功能】失败用例自动调用GitHub API创建Issue，打通评测与缺陷管理
【设计思想】测试与缺陷管理闭环，失败自动提单，符合企业工作流
"""
import os
import requests
from typing import Optional

# 从环境变量读取GitHub Token
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")


def create_github_issue(
    repo: str,
    title: str,
    body: str,
    labels: Optional[list] = None
) -> dict:
    """
    在指定仓库创建GitHub Issue
    :param repo: 仓库名，格式：owner/repo
    :param title: Issue标题
    :param body: Issue内容
    :param labels: 标签列表
    :return: 创建结果
    """
    # 没有Token直接返回错误
    if not GITHUB_TOKEN:
        return {"error": "Missing GITHUB_TOKEN environment variable"}

    # GitHub Issue创建API
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    payload = {
        "title": title,
        "body": body,
        "labels": labels or []
    }

    # 发送POST请求创建Issue
    resp = requests.post(url, json=payload, headers=headers)

    # 200/201都表示创建成功
    if resp.status_code in (200, 201):
        return resp.json()

    return {
        "error": resp.text,
        "status_code": resp.status_code
    }
