"""
【模块定位】输出层 - 报告生成模块
【核心功能】多格式输出评测结果：CSV/JSON/HTML
【设计思想】输出与业务解耦，新增格式只加函数，不影响核心逻辑
"""
import csv
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# 报告模板目录
TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"

# 初始化模板环境
env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))


def write_csv(out_path: str, results: list):
    """
    输出CSV格式报告
    优势：Excel可直接打开，适合后续数据处理
    """
    fieldnames = [
        "id", "testcase_id", "model", "status",
        "exact_match", "ratio", "latency", "tokens", "output"
    ]

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for r in results:
            # 展开metrics字段，扁平化写入
            metrics = r.get("metrics", {})
            writer.writerow({
                "id": r.get("id"),
                "testcase_id": r.get("testcase_id"),
                "model": r.get("model"),
                "status": r.get("status"),
                "exact_match": metrics.get("exact_match"),
                "ratio": metrics.get("ratio"),
                "latency": r.get("latency"),
                "tokens": r.get("tokens"),
                "output": r.get("output"),
            })


def write_json(out_path: str, results: list):
    """
    输出JSON格式报告
    优势：结构化完整，适合程序二次处理
    """
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def write_html(out_path: str, results: list, summary: dict | None = None):
    """
    输出HTML格式报告
    优势：可视化好，适合汇报、查看
    """
    # 加载报告模板
    tpl = env.get_template("report/template.html.j2")
    # 渲染模板
    html = tpl.render(results=results, summary=summary or {})

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
