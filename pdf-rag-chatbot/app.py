"""
FastAPI 기반 웹 챗봇 API 서버
LlamaIndex + ChromaDB + Ollama를 활용한 PDF 기반 RAG 챗봇
"""
import os
import uuid
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from rag_chatbot_ollama import RAGChatbot
from database import db
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

# ValidationError 처리 (422 오류 상세 정보 표시)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """422 오류 발생 시 상세 정보 반환"""
    errors = exc.errors()
    error_details = []
    for error in errors:
        error_details.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "요청 데이터 검증 실패",
            "error": "ValidationError",
            "detail": error_details
        }
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


# ==================== User 관련 모델 ====================
class User(BaseModel):
    """사용자 모델"""
    id: int  # 시퀀스로 자동 생성되는 정수
    email: str
    name: str
    image: Optional[str] = None
    provider: Optional[str] = None
    provider_id: Optional[str] = None


class UserCreateRequest(BaseModel):
    """사용자 생성 요청 모델 (이메일 기반)"""
    email: str = Field(..., description="이메일 (중복 체크 기준)")
    name: str = Field(..., description="이름")
    image: Optional[str] = Field(None, description="프로필 이미지 URL")
    provider: Optional[str] = Field(None, description="인증 제공자 (google, etc.)")
    provider_id: Optional[str] = Field(None, description="인증 제공자 ID (google ID, etc.)")
    class Config:
        # 필드명을 유연하게 받기 위한 설정
        populate_by_name = True


class UserResponse(BaseResponse):
    """사용자 응답 모델"""
    success: bool = True
    user: Optional[User] = None


# ==================== Chat History 관련 모델 ====================
class Message(BaseModel):
    """메시지 모델"""
    role: str  # "user" | "bot"
    content: str


class ChatHistory(BaseModel):
    """채팅 기록 모델"""
    id: str
    title: str
    userId: int  # users 테이블의 id (INTEGER)
    createdAt: str
    updatedAt: str
    messages: List[Message]


class ChatCreateRequest(BaseModel):
    """채팅 생성 요청 모델"""
    title: str
    userId: str  # 프론트엔드에서 문자열로 전달되지만, 백엔드에서 INTEGER로 변환
    messages: List[Message]


class ChatUpdateRequest(BaseModel):
    """채팅 업데이트 요청 모델"""
    chatId: str = Field(..., description="채팅 ID")
    userId: str = Field(..., description="사용자 ID (문자열로 전달되지만 INTEGER로 변환)")
    title: str = Field(..., description="채팅 제목")
    messages: List[Message] = Field(..., description="메시지 목록")
    
    class Config:
        populate_by_name = True


class ChatResponseModel(BaseResponse):
    """채팅 응답 모델"""
    success: bool = True
    chat: Optional[ChatHistory] = None


class ChatListResponse(BaseResponse):
    """채팅 목록 응답 모델"""
    success: bool = True
    chats: List[ChatHistory] = []


@app.on_event("startup") #서버가 실행될 때 딱 한 번 실행
async def startup_event():
    """서버 시작 시 챗봇 및 데이터베이스 자동 초기화"""
    global chatbot
    print("=" * 60)
    print("🚀 서버 시작 중...")
    print("=" * 60)
    
    # 데이터베이스 연결
    try:
        print("🗄️  데이터베이스 연결 중...")
        await db.connect()
        print("✅ 데이터베이스 연결 완료!")
    except Exception as e:
        print(f"⚠️  데이터베이스 연결 실패: {e}")
        print("   API는 작동하지만 사용자 및 채팅 기록 기능이 제한됩니다.")
    
    # 챗봇 초기화
    print("=" * 60)
    print("🤖 챗봇을 자동으로 초기화합니다.")
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


@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 데이터베이스 연결 종료"""
    await db.close()


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


# ==================== User API 엔드포인트 ====================

@app.post("/api/users", response_model=UserResponse)
async def create_user(request: UserCreateRequest):
    """
    회원정보 조회/생성 (이메일 기반)
    - 이메일로 사용자 조회
    - 없으면 백엔드에서 자동 생성된 userId로 새 사용자 생성
    - 있으면 정보 업데이트 후 반환
    - NextAuth 로그인 성공 시 호출
    """
    try:
        # 데이터베이스 연결 확인
        if db.engine is None:
            raise HTTPException(
                status_code=503,
                detail=ErrorResponse(
                    success=False,
                    message="데이터베이스에 연결되지 않았습니다.",
                    error="DatabaseNotConnected",
                    detail="서버 시작 시 데이터베이스 연결에 실패했습니다. 데이터베이스가 실행 중인지 확인하세요."
                ).dict()
            )
        
        # 요청 데이터 로깅 (디버깅용)
        print(f"📥 받은 사용자 데이터: email={request.email}, name={request.name}, image={request.image}, provider={request.provider}")
        
        # 이메일 기반으로 사용자 조회/생성 (백엔드에서 userId 자동 생성 - SERIAL 시퀀스)
        user_data = await db.create_or_get_user_by_email(
            email=request.email,
            name=request.name,
            image=request.image,
            provider=request.provider,
            provider_id=request.provider_id
        )
        
        if user_data:
            user = User(
                id=user_data['id'],
                email=user_data['email'],
                name=user_data['name'],
                image=user_data.get('image'),
                provider=user_data.get('provider'),
                provider_id=user_data.get('provider_id')
            )
            return UserResponse(
                success=True,
                message="회원정보가 저장되었습니다.",
                user=user
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=ErrorResponse(
                    success=False,
                    message="회원정보 저장에 실패했습니다.",
                    error="DatabaseError"
                ).dict()
            )
    except Exception as e:
        # 에러 상세 정보 로깅
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ 회원정보 저장 오류:")
        print(f"   에러 메시지: {str(e)}")
        print(f"   상세 트레이스:")
        print(error_trace)
        
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                success=False,
                message="회원정보 저장 중 오류가 발생했습니다.",
                error="UserCreationError",
                detail=str(e)
            ).dict()
        )


# ==================== Chat History API 엔드포인트 ====================

@app.get("/api/chats", response_model=ChatListResponse)
async def get_chats(userId: str = Query(..., description="사용자 ID (문자열, INTEGER로 변환)")):
    """
    채팅 목록 조회
    - 특정 사용자의 모든 채팅 기록을 최신순으로 반환
    """
    try:
        # 문자열 userId를 INTEGER로 변환
        try:
            user_id_int = int(userId)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    success=False,
                    message="잘못된 사용자 ID 형식입니다.",
                    error="InvalidUserId",
                    detail="userId는 정수여야 합니다."
                ).dict()
            )
        chats_data = await db.get_chats_by_user(user_id_int)
        
        chats = []
        for chat_data in chats_data:
            # 채팅 목록에서는 메시지를 포함하지 않음 (성능 최적화)
            # 필요시 GET /api/chats/{chatId}로 개별 조회
            chat = ChatHistory(
                id=chat_data['id'],
                title=chat_data['title'],
                userId=chat_data['user_id'],
                createdAt=chat_data['created_at'].isoformat() if hasattr(chat_data['created_at'], 'isoformat') else str(chat_data['created_at']),
                updatedAt=chat_data['updated_at'].isoformat() if hasattr(chat_data['updated_at'], 'isoformat') else str(chat_data['updated_at']),
                messages=[]  # 목록 조회 시 메시지는 빈 배열
            )
            chats.append(chat)
        
        return ChatListResponse(
            success=True,
            message=f"{len(chats)}개의 채팅을 찾았습니다.",
            chats=chats
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                success=False,
                message="채팅 목록 조회 중 오류가 발생했습니다.",
                error="ChatListError",
                detail=str(e)
            ).dict()
        )


@app.get("/api/chats/{chat_id}", response_model=ChatResponseModel)
async def get_chat(chat_id: str, userId: str = Query(..., description="사용자 ID (문자열, INTEGER로 변환)")):
    """
    특정 채팅 조회
    - chat_id와 userId로 특정 채팅 기록을 조회
    """
    try:
        # 문자열 userId를 INTEGER로 변환
        try:
            user_id_int = int(userId)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    success=False,
                    message="잘못된 사용자 ID 형식입니다.",
                    error="InvalidUserId",
                    detail="userId는 정수여야 합니다."
                ).dict()
            )
        chat_data = await db.get_chat(chat_id, user_id_int)
        
        if not chat_data:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    success=False,
                    message="채팅을 찾을 수 없습니다.",
                    error="ChatNotFound"
                ).dict()
            )
        
        messages = [
            Message(role=msg['role'], content=msg['content'])
            for msg in chat_data['messages']
        ]
        chat = ChatHistory(
            id=chat_data['id'],
            title=chat_data['title'],
            userId=chat_data['user_id'],
            createdAt=chat_data['created_at'].isoformat() if hasattr(chat_data['created_at'], 'isoformat') else str(chat_data['created_at']),
            updatedAt=chat_data['updated_at'].isoformat() if hasattr(chat_data['updated_at'], 'isoformat') else str(chat_data['updated_at']),
            messages=messages
        )
        
        return ChatResponseModel(
            success=True,
            message="채팅을 성공적으로 조회했습니다.",
            chat=chat
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                success=False,
                message="채팅 조회 중 오류가 발생했습니다.",
                error="ChatRetrievalError",
                detail=str(e)
            ).dict()
        )


@app.post("/api/chats", response_model=ChatResponseModel)
async def create_chat(request: ChatCreateRequest):
    """
    새 채팅 생성
    - 새로운 채팅 기록을 생성하고 반환
    - chatId는 서버에서 자동 생성됩니다
    """
    try:
        # 요청 데이터 디버깅
        print("=" * 60)
        print("📥 POST /api/chats 요청 받음")
        print(f"   userId: {request.userId}")
        print(f"   title: {request.title}")
        print(f"   messages 개수: {len(request.messages)}")
        print(f"   messages 상세:")
        for idx, msg in enumerate(request.messages):
            print(f"      [{idx}] role={msg.role}, content={msg.content[:50]}...")
        print("=" * 60)
        
        # 데이터베이스 연결 확인
        if db.engine is None:
            print("❌ 데이터베이스 엔진이 None입니다!")
            raise HTTPException(
                status_code=503,
                detail=ErrorResponse(
                    success=False,
                    message="데이터베이스에 연결되지 않았습니다.",
                    error="DatabaseNotConnected"
                ).dict()
            )
        
        # 서버에서 chat_id 생성 (프론트엔드에서는 보내지 않음)
        chat_id = str(uuid.uuid4())
        print(f"🔍 생성된 chat_id: {chat_id}")
        
        messages_data = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        print(f"🔍 변환된 messages_data: {len(messages_data)}개")
        
        # 문자열 userId를 INTEGER로 변환
        try:
            user_id_int = int(request.userId)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    success=False,
                    message="잘못된 사용자 ID 형식입니다.",
                    error="InvalidUserId",
                    detail="userId는 정수여야 합니다."
                ).dict()
            )
        print(f"🔍 db.create_chat 호출 전: chat_id={chat_id}, title={request.title}, user_id={user_id_int}")
        chat_data = await db.create_chat(
            chat_id=chat_id,
            title=request.title,
            user_id=user_id_int,
            messages=messages_data
        )
        print(f"🔍 db.create_chat 호출 후: chat_data={chat_data is not None}")
        
        if not chat_data:
            raise HTTPException(
                status_code=500,
                detail=ErrorResponse(
                    success=False,
                    message="채팅 생성에 실패했습니다.",
                    error="ChatCreationError"
                ).dict()
            )
        
        messages = [
            Message(role=msg['role'], content=msg['content'])
            for msg in chat_data['messages']
        ]
        chat = ChatHistory(
            id=chat_data['id'],
            title=chat_data['title'],
            userId=chat_data['user_id'],
            createdAt=chat_data['created_at'].isoformat() if hasattr(chat_data['created_at'], 'isoformat') else str(chat_data['created_at']),
            updatedAt=chat_data['updated_at'].isoformat() if hasattr(chat_data['updated_at'], 'isoformat') else str(chat_data['updated_at']),
            messages=messages
        )
        
        return ChatResponseModel(
            success=True,
            message="채팅이 성공적으로 생성되었습니다.",
            chat=chat
        )
    except HTTPException:
        raise
    except Exception as e:
        # 상세 에러 로깅
        import traceback
        error_trace = traceback.format_exc()
        print("=" * 60)
        print("❌ POST /api/chats 에러 발생!")
        print(f"   에러 타입: {type(e).__name__}")
        print(f"   에러 메시지: {str(e)}")
        print(f"   상세 트레이스:")
        print(error_trace)
        print("=" * 60)
        
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                success=False,
                message="채팅 생성 중 오류가 발생했습니다.",
                error="ChatCreationError",
                detail=str(e)
            ).dict()
        )


@app.put("/api/chats", response_model=ChatResponseModel)
async def update_chat(request: ChatUpdateRequest):
    """
    채팅 업데이트
    - 기존 채팅의 제목과 메시지를 업데이트
    - 프론트엔드에서 chatId를 body에 포함하여 전송
    """
    try:
        # 프론트엔드에서 보낸 chatId 사용
        chat_id = request.chatId
        # 문자열 userId를 INTEGER로 변환
        try:
            user_id_int = int(request.userId)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    success=False,
                    message="잘못된 사용자 ID 형식입니다.",
                    error="InvalidUserId",
                    detail="userId는 정수여야 합니다."
                ).dict()
            )
        messages_data = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        chat_data = await db.update_chat(
            chat_id=chat_id,
            user_id=user_id_int,
            title=request.title,
            messages=messages_data
        )
        
        if not chat_data:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    success=False,
                    message="채팅을 찾을 수 없습니다.",
                    error="ChatNotFound"
                ).dict()
            )
        
        messages = [
            Message(role=msg['role'], content=msg['content'])
            for msg in chat_data['messages']
        ]
        chat = ChatHistory(
            id=chat_data['id'],
            title=chat_data['title'],
            userId=chat_data['user_id'],
            createdAt=chat_data['created_at'].isoformat() if hasattr(chat_data['created_at'], 'isoformat') else str(chat_data['created_at']),
            updatedAt=chat_data['updated_at'].isoformat() if hasattr(chat_data['updated_at'], 'isoformat') else str(chat_data['updated_at']),
            messages=messages
        )
        
        return ChatResponseModel(
            success=True,
            message="채팅이 성공적으로 업데이트되었습니다.",
            chat=chat
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                success=False,
                message="채팅 업데이트 중 오류가 발생했습니다.",
                error="ChatUpdateError",
                detail=str(e)
            ).dict()
        )


@app.delete("/api/chats/{chat_id}", response_model=BaseResponse)
async def delete_chat(chat_id: str, userId: str = Query(..., description="사용자 ID (문자열, INTEGER로 변환)")):
    """
    채팅 삭제
    - 특정 채팅 기록을 삭제
    """
    try:
        # 문자열 userId를 INTEGER로 변환
        try:
            user_id_int = int(userId)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    success=False,
                    message="잘못된 사용자 ID 형식입니다.",
                    error="InvalidUserId",
                    detail="userId는 정수여야 합니다."
                ).dict()
            )
        success = await db.delete_chat(chat_id, user_id_int)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    success=False,
                    message="채팅을 찾을 수 없습니다.",
                    error="ChatNotFound"
                ).dict()
            )
        
        return BaseResponse(
            success=True,
            message="채팅이 성공적으로 삭제되었습니다."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                success=False,
                message="채팅 삭제 중 오류가 발생했습니다.",
                error="ChatDeletionError",
                detail=str(e)
            ).dict()
        )



if __name__ == "__main__":
    # 서버 실행
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # 개발 모드 (코드 변경 시 자동 재시작)
    )

