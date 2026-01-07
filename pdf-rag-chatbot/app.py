"""
FastAPI 기반 웹 챗봇 API 서버
LlamaIndex + ChromaDB + Ollama를 활용한 PDF 기반 RAG 챗봇
"""
import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from rag_chatbot_ollama import RAGChatbot
import uvicorn

# FastAPI 앱 생성
app = FastAPI(
    title="PDF RAG 챗봇 API",
    version="1.0.0",
    description="LlamaIndex + ChromaDB + Ollama를 활용한 PDF 기반 RAG 챗봇 API",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# 정적 파일 서빙 (HTML 파일)
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception:
    pass  # static 디렉토리가 없어도 API는 작동

# CORS 설정 (프론트엔드에서 API 호출을 위해 필요)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용하세요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 챗봇 인스턴스 (서버 시작 시 한 번만 초기화)
chatbot: Optional[RAGChatbot] = None

# 세션 관리는 RAGChatbot 클래스 내부에서 처리


# ==================== 공통 응답 모델 ====================
class BaseResponse(BaseModel):
    """기본 응답 모델"""
    success: bool
    message: str = ""


class ErrorResponse(BaseResponse):
    """에러 응답 모델"""
    success: bool = False
    error: str
    detail: Optional[str] = None


# ==================== 채팅 관련 모델 ====================
class ChatRequest(BaseModel):
    """채팅 요청 모델"""
    question: str
    session_id: str = "default"


class ChatResponse(BaseResponse):
    """채팅 응답 모델"""
    success: bool = True
    answer: str
    session_id: str


class ChatResetRequest(BaseModel):
    """채팅 세션 초기화 요청"""
    session_id: str = "default"


class ChatResetResponse(BaseResponse):
    """채팅 세션 초기화 응답"""
    success: bool = True
    session_id: str


# ==================== 질문 관련 모델 ====================
class QueryRequest(BaseModel):
    """단일 질문 요청 모델"""
    question: str
    similarity_top_k: int = 5


class QueryResponse(BaseResponse):
    """단일 질문 응답 모델"""
    success: bool = True
    answer: str


# ==================== 초기화 관련 모델 ====================
class InitRequest(BaseModel):
    """챗봇 초기화 요청 모델"""
    pdf_directory: str = "pdfs"
    persist_dir: str = "./chroma_db"
    model_name: str = "qwen2.5:1.5b"


class InitResponse(BaseResponse):
    """챗봇 초기화 응답 모델"""
    success: bool = True


# ==================== 상태 확인 모델 ====================
class StatusResponse(BaseModel):
    """서버 상태 응답 모델"""
    status: str
    chatbot_initialized: bool
    message: str = "PDF RAG 챗봇 API"


@app.on_event("startup") #서버가 실행될 때 딱 한 번 실행
async def startup_event():
    """서버 시작 시 챗봇 자동 초기화"""
    global chatbot
    print("=" * 60)
    print("🚀 서버 시작 중... 챗봇을 자동으로 초기화합니다.")
    print("=" * 60)
    try:
        print("📦 Ollama 모델 로드 중...")
        # 빠른 응답을 위한 작은 모델 사용 (qwen2.5:1.5b 또는 llama3.2:1b)
        model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
        print(f"📝 사용할 모델: {model_name}")
        
        print("📚 PDF 파일 인덱싱 시작...")
        chatbot = RAGChatbot(model_name=model_name)
        
        print("=" * 60)
        print("✅ 챗봇 초기화 완료! 서버가 준비되었습니다.")
        print("=" * 60)
        print(f"🌐 웹 인터페이스: http://localhost:8000/static/index.html")
        print(f"📖 API 문서: http://localhost:8000/api/docs")
        print("=" * 60)
    except Exception as e:
        print("=" * 60)
        print(f"❌ 챗봇 초기화 실패: {e}")
        print("=" * 60)
        print("💡 해결 방법:")
        print("   1. Ollama 서버가 실행 중인지 확인: ollama serve")
        print("   2. 모델이 다운로드되었는지 확인: ollama list")
        print("   3. 모델이 없으면 다운로드: ollama pull qwen2.5:1.5b")
        print("   4. /api/init 엔드포인트를 통해 수동으로 초기화할 수 있습니다.")
        print("=" * 60)
        chatbot = None  # 초기화 실패 시 None으로 설정


@app.get("/", response_model=StatusResponse)
async def root():
    """
    API 루트 엔드포인트 - 서버 상태 확인
    """
    return StatusResponse(
        status="running",
        chatbot_initialized=chatbot is not None,
        message="PDF RAG 챗봇 API"
    )


@app.get("/api/health", response_model=StatusResponse)
async def health_check():
    """
    헬스 체크 엔드포인트
    """
    return StatusResponse(
        status="healthy",
        chatbot_initialized=chatbot is not None,
        message="서버가 정상적으로 실행 중입니다."
    )


@app.post("/api/init", response_model=InitResponse)
async def initialize_chatbot(request: InitRequest):
    """
    챗봇 초기화
    - 서버 시작 시 자동 초기화되지만, 수동으로도 가능합니다.
    """
    global chatbot
    try:
        chatbot = RAGChatbot(
            pdf_directory=request.pdf_directory,
            persist_dir=request.persist_dir,
            model_name=request.model_name
        )
        return InitResponse(
            success=True,
            message="챗봇 초기화가 완료되었습니다."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                success=False,
                message="챗봇 초기화에 실패했습니다.",
                error="InitializationError",
                detail=str(e)
            ).dict()
        )


@app.post("/api/query", response_model=QueryResponse)
async def query_chatbot(request: QueryRequest):
    """
    단일 질문에 대한 답변 생성
    - 대화 기록을 유지하지 않는 단일 질문/답변입니다.
    """
    if chatbot is None:
        raise HTTPException(
            status_code=503,
            detail=ErrorResponse(
                success=False,
                message="챗봇이 초기화되지 않았습니다.",
                error="ChatbotNotInitialized",
                detail="/api/init 엔드포인트를 먼저 호출하세요."
            ).dict()
        )
    
    try:
        answer = chatbot.query(
            question=request.question,
            similarity_top_k=request.similarity_top_k
        )
        return QueryResponse(
            success=True,
            answer=answer,
            message="질문이 성공적으로 처리되었습니다."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                success=False,
                message="질문 처리 중 오류가 발생했습니다.",
                error="QueryError",
                detail=str(e)
            ).dict()
        )


@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_bot(request: ChatRequest):
    """
    대화형 채팅 (대화 기록 지원)
    - 같은 session_id를 사용하면 대화 기록이 유지됩니다.
    - Next.js 등 프론트엔드에서 사용하기 적합한 엔드포인트입니다.
    """
    if chatbot is None:
        raise HTTPException(
            status_code=503,
            detail=ErrorResponse(
                success=False,
                message="챗봇이 초기화되지 않았습니다.",
                error="ChatbotNotInitialized",
                detail="/api/init 엔드포인트를 먼저 호출하세요."
            ).dict()
        )
    
    try:
        # RAGChatbot 클래스의 chat() 메서드가 세션 관리를 처리합니다
        response_text = chatbot.chat(
            question=request.question,
            session_id=request.session_id
        )
        
        return ChatResponse(
            success=True,
            answer=response_text,
            session_id=request.session_id,
            message="답변이 성공적으로 생성되었습니다."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                success=False,
                message="채팅 처리 중 오류가 발생했습니다.",
                error="ChatError",
                detail=str(e)
            ).dict()
        )


@app.delete("/api/chat/session/{session_id}", response_model=ChatResetResponse)
async def reset_chat_session(session_id: str):
    """
    특정 세션의 대화 기록 초기화
    - DELETE 메서드를 사용하여 RESTful하게 구현
    """
    if chatbot is None:
        raise HTTPException(
            status_code=503,
            detail=ErrorResponse(
                success=False,
                message="챗봇이 초기화되지 않았습니다.",
                error="ChatbotNotInitialized",
                detail="/api/init 엔드포인트를 먼저 호출하세요."
            ).dict()
        )
    
    chatbot.reset_session(session_id)
    return ChatResetResponse(
        success=True,
        session_id=session_id,
        message=f"세션 '{session_id}'의 대화 기록이 초기화되었습니다."
    )



if __name__ == "__main__":
    # 서버 실행
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # 개발 모드 (코드 변경 시 자동 재시작)
    )

