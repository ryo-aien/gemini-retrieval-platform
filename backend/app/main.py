"""FastAPI main application"""
import os
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from app.models.schemas import HealthResponse, ErrorResponse

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="gemini-retrieval-platform API",
    description="Document interaction system with Gemini File Search",
    version="0.1.0",
)

# CORS configuration
# 環境変数ALLOWED_ORIGINSからカンマ区切りで取得
# デフォルトは開発環境用のlocalhost + 統合デプロイの場合は同一オリジンなのでCORSは不要だが、
# 2サービスデプロイの場合に備えて設定可能にしておく
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    allowed_origins = allowed_origins_env.split(",")
else:
    # デフォルトは開発環境用
    allowed_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://frontend:5173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat()
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "gemini-retrieval-platform",
        "version": "0.1.0",
        "status": "running"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail=str(exc)
        ).model_dump()
    )


# Import and include routers
from app.routes import stores, documents, chat, report

app.include_router(stores.router, prefix="/api", tags=["stores"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(report.router, prefix="/api", tags=["report"])
