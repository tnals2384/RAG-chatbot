# 서비스 아키텍처 및 동작 원리

## 📐 전체 아키텍처 개요

이 서비스는 **RAG (Retrieval-Augmented Generation)** 기술을 활용한 PDF 문서 기반 챗봇입니다. 사용자가 질문하면 PDF 문서에서 관련 정보를 검색하여 답변을 생성합니다.

```text
┌─────────────┐
│   사용자    │
│  (브라우저) │
└──────┬──────┘
       │ HTTP 요청
       ▼
┌─────────────────────────────────────┐
│      FastAPI 웹 서버 (app.py)       │
│  - RESTful API 엔드포인트 제공       │
│  - 세션 관리 및 대화 기록 유지      │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│    RAGChatbot (rag_chatbot_ollama) │
│  - 질문 처리 및 답변 생성           │
│  - 벡터 검색 및 LLM 통합            │
└──────┬──────────────────────────────┘
       │
       ├─────────────────┬──────────────────┐
       ▼                 ▼                   ▼
┌─────────────┐  ┌──────────────┐  ┌─────────────┐
│  ChromaDB   │  │   Ollama     │  │ HuggingFace │
│ (벡터 DB)   │  │   (LLM)      │  │ (Embedding) │
│             │  │              │  │             │
│ - PDF 벡터  │  │ - 답변 생성  │  │ - 텍스트    │
│   인덱스    │  │ - 대화 맥락  │  │   벡터화    │
│   저장      │  │   유지       │  │             │
└─────────────┘  └──────────────┘  └─────────────┘
```

**복사하기 쉬운 버전:**

```
사용자 (브라우저)
    ↓ HTTP 요청
FastAPI 웹 서버 (app.py)
    - RESTful API 엔드포인트 제공
    - 세션 관리 및 대화 기록 유지
    ↓
RAGChatbot (rag_chatbot_ollama)
    - 질문 처리 및 답변 생성
    - 벡터 검색 및 LLM 통합
    ↓
    ├─→ ChromaDB (벡터 DB)
    │   - PDF 벡터 인덱스 저장
    │
    ├─→ Ollama (LLM)
    │   - 답변 생성
    │   - 대화 맥락 유지
    │
    └─→ HuggingFace (Embedding)
        - 텍스트 벡터화
```

## 🔄 RAG (Retrieval-Augmented Generation) 동작 원리

RAG는 두 단계로 구성됩니다:

### 1. Retrieval (검색) 단계

- 사용자 질문을 **벡터로 변환** (Embedding)
- ChromaDB에서 **유사한 문서 청크 검색**
- 가장 관련성 높은 문서들을 추출

### 2. Generation (생성) 단계

- 검색된 문서를 **컨텍스트로 제공**
- Ollama LLM이 컨텍스트를 바탕으로 **답변 생성**
- 문서에 없는 정보는 답변하지 않음

## 🧩 주요 컴포넌트 상세 설명

### 1. FastAPI 웹 서버 (`app.py`)

**역할:**

- 웹 인터페이스와 API 제공
- HTTP 요청 처리 및 응답 반환
- 세션 관리 및 대화 기록 유지

**주요 기능:**

- **서버 시작 시**: `pdfs` 디렉토리의 모든 PDF를 자동으로 인덱싱
- **세션 관리**: 각 사용자 세션별로 `chat_engine` 저장하여 대화 기록 유지
- **CORS 설정**: 프론트엔드에서 API 호출 허용

**API 엔드포인트:**

- `GET /`: 서버 상태 확인
- `GET /health`: 헬스 체크
- `POST /chat`: 대화형 채팅 (대화 기록 유지)
- `POST /query`: 단일 질문 처리 (대화 기록 없음)
- `POST /init`: 수동 초기화 (선택사항)

### 2. RAGChatbot 클래스 (`rag_chatbot_ollama.py`)

**역할:**

- PDF 문서 처리 및 인덱싱
- 벡터 검색 수행
- LLM과의 통합 관리

**주요 메서드:**

#### `__init__()` - 초기화

```python
1. Ollama LLM 모델 로드
2. HuggingFace Embedding 모델 로드
3. ChromaDB 클라이언트 초기화
4. PDF 문서 인덱싱 (서버 시작 시 자동)
```

#### `_initialize_index()` - 인덱스 초기화

```python
1. 기존 ChromaDB 컬렉션 삭제 (항상 최신 PDF 반영)
2. pdfs 디렉토리의 모든 PDF 파일 읽기
3. PDF를 텍스트로 변환 및 청크 분할
4. 각 청크를 벡터로 변환 (Embedding)
5. ChromaDB에 벡터 인덱스 저장
```

#### `chat()` - 대화형 채팅

```python
1. 사용자 질문을 벡터로 변환
2. ChromaDB에서 유사한 문서 검색 (similarity_top_k=7)
3. 관련 문서가 없으면 "정보 없음" 메시지 반환
4. 검색된 문서를 컨텍스트로 제공
5. Ollama LLM이 컨텍스트 기반 답변 생성
6. 답변 반환
```

### 3. ChromaDB (벡터 데이터베이스)

**역할:**

- PDF 문서의 벡터 인덱스 저장
- 유사도 기반 빠른 검색 제공

**데이터 구조:**

- **컬렉션 이름**: `pdf_documents`
- **저장 위치**: `./chroma_db/` 디렉토리
- **데이터 형식**:
  - 문서 ID
  - 벡터 (Embedding 벡터)
  - 메타데이터 (원본 텍스트, 파일명 등)

**검색 과정:**

1. 질문 텍스트 → Embedding 벡터 변환
2. ChromaDB에서 코사인 유사도 계산
3. 유사도가 높은 상위 K개 문서 반환

### 4. Ollama (대형 언어 모델)

**역할:**

- 자연어 질문 이해
- 검색된 문서를 바탕으로 답변 생성
- 대화 맥락 유지

**사용 모델:**

- 기본값: `qwen2.5:1.5b` (빠른 응답)
- 설정 가능: `.env` 파일에서 `OLLAMA_MODEL` 변경

**시스템 프롬프트:**

```
- 자세하고 친절하게 답변
- 문서에 없는 정보는 추측하지 않음
- 최소 2-3문장 이상으로 자세하게 작성
```

### 5. HuggingFace Embedding 모델

**역할:**

- 텍스트를 벡터로 변환
- 한국어 지원

**사용 모델:**

- `jhgan/ko-sroberta-multitask` (한국어 특화)

**동작:**

- PDF 텍스트 청크 → 벡터 변환 (인덱싱 시)
- 사용자 질문 → 벡터 변환 (검색 시)
- 벡터 간 유사도 계산으로 관련 문서 찾기

## 📊 데이터 흐름도

### 서버 시작 시 (초기화)

```
1. app.py 실행
   ↓
2. @app.on_event("startup") 트리거
   ↓
3. RAGChatbot 초기화
   ├─ Ollama LLM 로드
   ├─ HuggingFace Embedding 모델 로드
   └─ _initialize_index() 호출
      ├─ pdfs 디렉토리 스캔
      ├─ PDF 파일 읽기 (SimpleDirectoryReader)
      ├─ 텍스트 청크 분할 (chunk_size=1024)
      ├─ 각 청크를 벡터로 변환 (Embedding)
      └─ ChromaDB에 저장
   ↓
4. 서버 준비 완료
```

### 사용자 질문 처리 과정

```
사용자 질문 입력
   ↓
[프론트엔드] POST /chat 요청
   ↓
[FastAPI] chat_with_bot() 호출
   ↓
[RAGChatbot] chat() 메서드 실행
   ├─ 1. 질문을 벡터로 변환 (Embedding)
   ├─ 2. ChromaDB에서 유사 문서 검색
   │   └─ similarity_top_k=7 (상위 7개)
   ├─ 3. 관련 문서 확인
   │   └─ 없으면 → "정보 없음" 반환
   └─ 4. 검색된 문서를 컨텍스트로 제공
       ↓
[Ollama LLM] 답변 생성
   ├─ 시스템 프롬프트 적용
   ├─ 검색된 문서 컨텍스트 포함
   ├─ 이전 대화 기록 참조 (세션별)
   └─ 답변 텍스트 생성
       ↓
[프론트엔드] 마크다운 포맷팅
   ├─ **텍스트** → <strong>텍스트</strong>
   ├─ 줄바꿈 처리
   ├─ 리스트 포맷팅
   └─ 사용자에게 표시
```

## 🔍 상세 동작 과정

### 1. PDF 인덱싱 과정

```python
# _create_index() 메서드 내부

# 1단계: PDF 문서 수집 (텍스트 추출) - 별도 처리
documents = SimpleDirectoryReader("pdfs", required_exts=[".pdf"]).load_data()
# → PDF 파일을 읽어서 Document 객체로 변환
# → 아직 청크 분할은 안 됨 (전체 문서 단위)
# → 이 단계는 SimpleDirectoryReader가 담당

# 2-4단계: 인덱스 생성 (분할 + 임베딩 + 저장을 한꺼번에 처리)
VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context
)
# 이 메서드가 내부적으로 다음을 한꺼번에 수행:
#
# 2단계: 텍스트 청크 분할
#    - Settings.chunk_size=1024 문자 사용
#    - Settings.chunk_overlap=200 문자 (연속성 유지)
#    예: "문서 내용..." → [청크1, 청크2, 청크3, ...]
#
# 3단계: 벡터 변환 (Embedding)
#    - Settings.embed_model 사용 (HuggingFace 모델)
#    각 청크 → 768차원 벡터
#    예: 청크1 → [0.123, -0.456, 0.789, ...]
#
# 4단계: ChromaDB 저장
#    {
#      id: "doc_1_chunk_1",
#      embedding: [0.123, -0.456, ...],
#      metadata: {
#        text: "원본 텍스트",
#        file_name: "본사 근무 가이드북.pdf"
#      }
#    }
```

**중요**:

- **1단계 (문서 읽기)**: `SimpleDirectoryReader().load_data()`가 별도로 처리
- **2-4단계 통합**: `VectorStoreIndex.from_documents()`가 **분할, 임베딩, 저장을 한꺼번에 처리**
- 개발자가 별도로 청크 분할이나 임베딩을 호출할 필요가 없습니다.

### 2. 질문 검색 과정

```python
# chat() 메서드 내부

1. 질문 벡터화
   "연차는 어떻게 신청하나요?"
   → Embedding 모델
   → [0.234, -0.567, 0.890, ...]

2. 유사도 검색
   ChromaDB.query(
     query_embeddings=[0.234, -0.567, ...],
     n_results=7
   )
   → 코사인 유사도 계산
   → 상위 7개 문서 반환

3. 컨텍스트 구성
   검색된 문서들을 하나의 컨텍스트로 결합
   "문서1: 연차 신청은..."
   "문서2: 신청 기한은..."
   ...
```

### 3. 답변 생성 과정

```python
# Ollama LLM 호출

프롬프트 구성:
"""
시스템: 당신은 친절하고 자세하게 답변하는 어시스턴트입니다.
        문서에 없는 정보는 추측하지 마세요.

컨텍스트:
[검색된 문서 1]
[검색된 문서 2]
...

이전 대화:
사용자: 연차는 어떻게 신청하나요?
봇: 연차 신청은...

현재 질문:
사용자: 그건 몇일 전에 신청해야 하나요?
"""

LLM 처리:
1. 컨텍스트 분석
2. 질문 이해
3. 이전 대화 맥락 참조
4. 답변 생성
   → "연차는 최소 3일 전에 신청해야 합니다..."
```

## 🌐 웹 인터페이스 동작

### 프론트엔드 (`static/index.html`)

**주요 기능:**

1. **세션 관리**

   ```javascript
   const SESSION_ID = "session_" + Date.now() + "_" + Math.random();
   // 페이지 로드 시 고유 세션 ID 생성
   // 같은 세션에서 대화 기록 유지
   ```

2. **메시지 전송**

   ```javascript
   POST /chat
   {
     question: "사용자 질문",
     session_id: "session_1234567890"
   }
   ```

3. **마크다운 포맷팅**

   - `**텍스트**` → `<strong>텍스트</strong>`
   - 줄바꿈 처리
   - 리스트 포맷팅
   - 번호 리스트 처리

4. **로딩 표시**
   - 질문 전송 시 봇 말풍선에 타이핑 인디케이터 표시
   - 답변 수신 시 실제 답변으로 교체

## 🔐 세션 관리 및 대화 기록

### 세션별 chat_engine 저장

```python
# app.py

chat_engines: dict = {}  # 전역 딕셔너리

# 첫 질문 시
if session_id not in chat_engines:
    chat_engines[session_id] = chatbot.index.as_chat_engine(
        chat_mode="context",  # 대화 맥락 유지
        similarity_top_k=7,
        system_prompt=custom_prompt
    )

# 이후 질문 시
chat_engine = chat_engines[session_id]  # 같은 엔진 재사용
response = chat_engine.chat(question)   # 이전 대화 맥락 포함
```

### 대화 기록 유지 메커니즘

1. **LlamaIndex의 chat_mode="context"**

   - 이전 대화를 자동으로 컨텍스트에 포함
   - 최근 N개 대화 기록 유지

2. **세션별 엔진 분리**
   - 각 사용자(세션)마다 독립적인 대화 기록
   - 페이지 새로고침 시 새 세션 시작

## ⚙️ 설정 및 파라미터

### 주요 설정값

```python
# rag_chatbot_ollama.py

# 청크 크기
Settings.chunk_size = 1024        # 각 청크의 최대 문자 수
Settings.chunk_overlap = 200      # 청크 간 겹치는 문자 수

# 검색 설정
similarity_top_k = 7              # 검색할 문서 개수

# LLM 설정
temperature = 0.8                 # 답변 창의성 (0.0~1.0)
request_timeout = 120.0           # 요청 타임아웃 (초)
```

### 환경 변수

```env
# .env 파일

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:1.5b
```

## 📈 성능 최적화

### 1. 인덱싱 최적화

- **청크 크기**: 1024 문자 (너무 작으면 검색 정확도 ↓, 너무 크면 관련성 ↓)
- **청크 오버랩**: 200 문자 (문맥 연속성 유지)

### 2. 검색 최적화

- **similarity_top_k**: 7개 (충분한 컨텍스트, 빠른 검색)
- **ChromaDB**: 인메모리 검색으로 빠른 응답

### 3. 답변 생성 최적화

- **작은 모델 사용**: `qwen2.5:1.5b` (빠른 응답)
- **Temperature 조정**: 0.8 (자세한 답변, 적절한 속도)

## 🔒 보안 및 제한사항

### 보안

- CORS 설정: 개발 환경에서는 `allow_origins=["*"]` (프로덕션에서는 특정 도메인만 허용 권장)
- 로컬 실행: Ollama와 Embedding 모델이 로컬에서 실행되어 데이터 유출 위험 최소화

### 제한사항

- **PDF 텍스트만 처리**: 이미지로 된 텍스트(스캔본)는 OCR 필요
- **메모리 사용**: 큰 PDF 파일은 많은 메모리 필요
- **응답 시간**: 첫 실행 시 모델 다운로드로 시간 소요

## 🚀 확장 가능성

### 향후 개선 방향

1. **OCR 지원**: 스캔본 PDF 처리
2. **멀티 모달**: 이미지, 표 등 다양한 형식 지원
3. **캐싱**: 자주 묻는 질문 캐싱으로 응답 속도 향상
4. **사용자 인증**: 세션별 사용자 구분
5. **대화 내보내기**: 대화 기록 저장 및 내보내기

## 📚 참고 자료

- **LlamaIndex**: https://docs.llamaindex.ai/
- **ChromaDB**: https://www.trychroma.com/
- **Ollama**: https://ollama.ai/
- **HuggingFace**: https://huggingface.co/
