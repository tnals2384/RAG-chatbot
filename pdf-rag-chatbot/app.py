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

# 세션별 채팅 엔진 저장 (대화 기록 유지용)
chat_engines: dict = {}


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


@app.on_event("startup")
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


@app.get("/health", response_model=StatusResponse)
async def health_check_legacy():
    """
    헬스 체크 엔드포인트 (레거시 호환용)
    - 기존 코드와의 호환성을 위해 유지
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
        # 세션별로 chat_engine 재사용 (대화 기록 유지)
        if request.session_id not in chat_engines:
            # 커스텀 시스템 프롬프트 (자세한 답변 유도)
            custom_prompt = (
                "당신은 친절하고 자세하게 답변하는 어시스턴트입니다.\n"
                "답변할 때 다음을 지켜주세요:\n"
                "1. 제공된 문서의 정보를 바탕으로 자세하고 친절하게 설명하세요.\n"
                "2. 가능한 한 구체적이고 실용적인 정보를 포함하세요.\n"
                "3. 단계별 설명이 필요한 경우 명확하게 나누어 설명하세요.\n"
                "4. 관련 정보가 없는 경우에만 \"죄송합니다. 해당 정보를 찾을 수 없습니다. 다른 질문을 해주시면 도와드리겠습니다.\"라고 답변하세요.\n"
                "5. 답변은 최소 2-3문장 이상으로 자세하게 작성하세요."
            )
            
            chat_engines[request.session_id] = chatbot.index.as_chat_engine(
                chat_mode="context",
                similarity_top_k=7,
                verbose=False,
                system_prompt=custom_prompt
            )
        
        chat_engine = chat_engines[request.session_id]
        
        # 유사한 문서 검색하여 관련 정보 존재 여부 확인
        retriever = chatbot.index.as_retriever(similarity_top_k=7)
        nodes = retriever.retrieve(request.question)
        
        # 관련 문서가 없는 경우
        if not nodes or len(nodes) == 0:
            return ChatResponse(
                success=True,
                answer="죄송합니다. 해당 정보를 찾을 수 없습니다. 다른 질문을 해주시면 도와드리겠습니다.",
                session_id=request.session_id,
                message="관련 문서를 찾을 수 없습니다."
            )
        
        # 정상적인 답변 생성 (대화 기록 유지)
        response = chat_engine.chat(request.question)
        response_text = str(response)
        
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
    if session_id in chat_engines:
        del chat_engines[session_id]
        return ChatResetResponse(
            success=True,
            session_id=session_id,
            message=f"세션 '{session_id}'의 대화 기록이 초기화되었습니다."
        )
    return ChatResetResponse(
        success=True,
        session_id=session_id,
        message=f"세션 '{session_id}'가 존재하지 않습니다."
    )


@app.post("/api/chat/reset", response_model=ChatResetResponse)
async def reset_chat_session_post(request: ChatResetRequest):
    """
    특정 세션의 대화 기록 초기화 (POST 메서드)
    - DELETE 메서드를 지원하지 않는 클라이언트를 위한 대안
    """
    session_id = request.session_id
    if session_id in chat_engines:
        del chat_engines[session_id]
        return ChatResetResponse(
            success=True,
            session_id=session_id,
            message=f"세션 '{session_id}'의 대화 기록이 초기화되었습니다."
        )
    return ChatResetResponse(
        success=True,
        session_id=session_id,
        message=f"세션 '{session_id}'가 존재하지 않습니다."
    )


if __name__ == "__main__":
    # 서버 실행
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # 개발 모드 (코드 변경 시 자동 재시작)
    )

