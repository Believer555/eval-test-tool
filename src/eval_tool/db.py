"""
【模块定位】数据层 - ORM持久化模块
【核心功能】基于SQLAlchemy实现SQLite数据库访问，定义四个核心业务实体
【数据模型】Requirement → TestCase → TestRun → Bug 全链路追溯
【设计思想】ORM抽象，底层数据库可替换，业务代码无需修改
"""
import os
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, DateTime, Text, JSON, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 项目根目录路径
BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
# 数据库文件路径，支持环境变量自定义
DB_PATH = os.environ.get(
    "EVAL_TOOL_DB",
    os.path.join(BASE_DIR, "data", "eval_tool.db")
)

# 创建数据库引擎，echo=False关闭SQL日志，future=True兼容新版本写法
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
# 创建会话工厂，autoflush/autocommit关闭，手动控制事务
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
# ORM实体基类
Base = declarative_base()


class Requirement(Base):
    """需求实体：记录需求条目，是测试用例的来源"""
    __tablename__ = "requirements"

    id = Column(String, primary_key=True)          # 主键，字符串类型
    title = Column(String, nullable=False)         # 需求标题
    text = Column(Text, nullable=False)            # 需求详细内容
    source = Column(String, nullable=True)          # 需求来源（文件路径/URL）
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间


class TestCase(Base):
    """测试用例实体：最小测试单元，可关联到具体需求"""
    __tablename__ = "testcases"

    id = Column(String, primary_key=True)          # 用例ID
    req_id = Column(String, nullable=True)          # 关联的需求ID，可选
    title = Column(String, nullable=False)         # 用例标题
    steps = Column(Text, nullable=True)            # 测试步骤（文本/JSON）
    input = Column(Text, nullable=True)            # 模型输入内容
    expected = Column(Text, nullable=True)         # 预期输出结果
    priority = Column(Integer, default=3)          # 优先级，1最高，3普通
    author = Column(String, nullable=True)          # 用例作者
    created_at = Column(DateTime, default=datetime.utcnow)


class TestRun(Base):
    """执行记录实体：记录每一次用例执行的完整信息"""
    __tablename__ = "testruns"

    id = Column(String, primary_key=True)          # 运行记录ID（UUID）
    testcase_id = Column(String, nullable=False)    # 关联的测试用例ID
    model = Column(String, nullable=False)         # 执行使用的模型
    prompt = Column(Text, nullable=True)           # 实际发送的完整Prompt
    output = Column(Text, nullable=True)           # 模型实际输出
    metrics = Column(JSON, nullable=True)          # 评测指标结果（JSON格式）
    status = Column(String, nullable=True)         # 执行状态：pass/fail/error
    latency = Column(Integer, nullable=True)       # 调用耗时，单位毫秒
    tokens = Column(Integer, nullable=True)        # 消耗的token数量
    run_at = Column(DateTime, default=datetime.utcnow)  # 执行时间


class Bug(Base):
    """缺陷实体：失败用例对应的缺陷记录，可关联外部Issue"""
    __tablename__ = "bugs"

    id = Column(String, primary_key=True)          # 缺陷ID
    testrun_id = Column(String, nullable=False)    # 关联的执行记录ID
    title = Column(String, nullable=False)         # 缺陷标题
    body = Column(Text, nullable=True)             # 缺陷详细描述
    issue_url = Column(String, nullable=True)      # 外部Issue链接
    status = Column(String, default="open")        # 缺陷状态：open/closed
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """初始化数据库：创建数据表，首次运行时调用"""
    # 确保数据目录存在，不存在则创建
    data_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)

    # 根据实体定义创建所有数据表
    Base.metadata.create_all(engine)
