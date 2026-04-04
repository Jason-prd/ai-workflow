"""
测试配置和共享 Fixtures
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os

# 设置测试环境变量
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["OPENAI_API_KEY"] = "sk-test-openai-key"

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.workflow import Workflow, WorkflowStatus
from app.services.auth_service import get_password_hash


# 创建测试数据库引擎（内存SQLite）
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆盖数据库依赖，返回测试数据库会话"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# 覆盖应用的数据库依赖
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db():
    """每个测试函数使用独立的数据库会话"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """返回测试客户端"""
    yield TestClient(app)


@pytest.fixture
def test_user(db):
    """创建一个测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("TestPassword123")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_user2(db):
    """创建第二个测试用户（用于数据隔离测试）"""
    user = User(
        username="testuser2",
        email="test2@example.com",
        password_hash=get_password_hash("TestPassword456")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_token(client, test_user):
    """获取测试用户的JWT令牌"""
    response = client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "TestPassword123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """返回认证请求头"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def auth_token2(client, test_user2):
    """获取第二个测试用户的JWT令牌"""
    response = client.post(
        "/api/auth/login",
        json={"username": "testuser2", "password": "TestPassword456"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers2(auth_token2):
    """返回第二个用户的认证请求头"""
    return {"Authorization": f"Bearer {auth_token2}"}


@pytest.fixture
def sample_workflow_data():
    """示例工作流数据"""
    return {
        "name": "测试工作流",
        "description": "用于测试的工作流",
        "trigger_config": {"type": "manual"},
        "nodes": [
            {
                "id": "trigger_1",
                "type": "trigger",
                "name": "手动触发器",
                "config": {"type": "manual"}
            },
            {
                "id": "ai_1",
                "type": "ai_task",
                "name": "AI处理",
                "config": {
                    "model": "gpt-4o-mini",
                    "prompt": "请处理以下内容：{{input}}",
                    "temperature": 0.7
                }
            }
        ]
    }


@pytest.fixture
def sample_workflow(client, auth_headers, sample_workflow_data):
    """创建一个示例工作流"""
    response = client.post(
        "/api/workflows",
        json=sample_workflow_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def published_workflow(client, auth_headers, sample_workflow_data):
    """创建一个已发布的工作流"""
    response = client.post(
        "/api/workflows",
        json=sample_workflow_data,
        headers=auth_headers
    )
    workflow_id = response.json()["id"]
    
    # 发布工作流
    publish_response = client.post(
        f"/api/workflows/{workflow_id}/publish",
        headers=auth_headers
    )
    assert publish_response.status_code == 200
    return publish_response.json()
