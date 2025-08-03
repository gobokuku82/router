import sys
from pathlib import Path

# 경로 설정 
current_file = Path(__file__).resolve()
app_dir = current_file.parent  # backend/app
backend_dir = app_dir.parent    # backend

# backend를 Python 경로에 추가하여 app.* 형태로 import 가능하게 함
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

print(f"[PATH] Added to sys.path: {backend_dir}")
print(f"[PATH] Current working dir: {Path.cwd()}")

# 이제 일반적인 import 가능
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# .env 파일 로드
# 1. backend/app/.env 우선
# 2. 프로젝트 루트의 .env 
env_paths = [
    app_dir / ".env",
    backend_dir.parent / ".env"
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[ENV] Loaded .env from: {env_path}")
        break

# OPENAI_API_KEY 확인
if os.getenv("OPENAI_API_KEY"):
    print("[ENV] OPENAI_API_KEY is set")
else:
    print("[WARNING] OPENAI_API_KEY is not set")

# 이제 상대 경로 import 대신 app.으로 시작하는 import 사용
from app.api.router_api import router
print("[OK] router_api imported successfully")

# 간단한 테스트 라우터 추가
try:
    from app.api.router_api_simple import router as simple_router
    print("[OK] router_api_simple imported successfully")
except Exception as e:
    print(f"[WARNING] Failed to import router_api_simple: {e}")
    simple_router = None

app = FastAPI(title="Multi-Agent Router API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록 - /api prefix로 통일
app.include_router(router, prefix="/api")
print("[OK] Router registered at /api")

# 간단한 테스트 라우터 등록
if simple_router:
    app.include_router(simple_router, prefix="/api")
    print("[OK] Simple router registered at /api")

# 헬스 체크
@app.get("/health")
def health():
    return {"status": "ok"}

# API 경로 확인용
@app.get("/api-routes")
def get_api_routes():
    routes = []
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if route.methods else []
            })
    return {"routes": routes}

# 메인 실행
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("[FastAPI Server]")
    print("Running at: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("API Routes: http://localhost:8000/api-routes")
    print("Health Check: http://localhost:8000/health")
    print("Stop: Ctrl+C")
    print("="*60 + "\n")
    
    # reload를 위해서는 문자열로 전달해야 함
    # 하지만 현재 경로 문제로 인해 reload 없이 실행
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,  # reload 비활성화
        log_level="info"
    )