"""
AI自动化工作流 - 后端主入口
"""
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import init_db
from app.api import auth, workflows, executions, feishu, nodes
from app.integrations import feishu_bot_router
from app.integrations.feishu_calendar_trigger import feishu_calendar_poller


# 日历轮询任务句柄
_calendar_poller_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    init_db()
    
    # 启动日历轮询任务
    global _calendar_poller_task
    # 日历轮询器会从数据库动态发现已配置的触发器，无需在此检查
    _calendar_poller_task = asyncio.create_task(feishu_calendar_poller.start())
    
    yield
    
    # 关闭日历轮询任务
    feishu_calendar_poller.stop()
    if _calendar_poller_task:
        _calendar_poller_task.cancel()
        try:
            await _calendar_poller_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="AI自动化工作流",
    description="AI驱动的自动化工作流编排系统 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(workflows.router)
app.include_router(executions.router)
app.include_router(feishu.router)
app.include_router(nodes.router)
# 飞书集成路由
app.include_router(feishu_bot_router)


@app.get("/")
async def root():
    """健康检查"""
    return {"status": "ok", "message": "AI自动化工作流服务运行中"}


@app.get("/api/health")
async def health():
    """健康检查接口"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
