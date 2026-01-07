# PDF 기반 RAG 챗봇 (Ollama 사용)

LlamaIndex, ChromaDB, Ollama를 활용한 PDF 문서 기반 RAG(Retrieval-Augmented Generation) 챗봇입니다.

## 🌟 주요 특징

- **완전 무료**: Ollama는 로컬에서 실행되므로 API 비용이 없습니다
- **오프라인 동작**: 인터넷 연결 없이도 작동합니다
- **한국어 지원**: 한국어 PDF와 질문을 모두 지원합니다
- **효율적인 검색**: ChromaDB를 사용한 빠른 벡터 검색
- **대화형 인터페이스**: 자연스러운 대화형 챗봇

## 📋 사전 준비사항

### 1. Ollama 설치

Ollama를 설치해야 합니다. 다음 사이트에서 다운로드하세요:

- Windows: https://ollama.ai/download
- macOS: `brew install ollama` 또는 https://ollama.ai/download
- Linux: `curl -fsSL https://ollama.ai/install.sh | sh`

### 2. Ollama 서버 실행

Ollama 설치 후 서버가 자동으로 시작됩니다. 수동으로 시작하려면:

```bash
ollama serve
```

### 3. Ollama 모델 다운로드

한국어 지원이 좋은 모델을 추천합니다:

```bash
# 한국어 지원이 좋은 모델 (추천)
ollama pull llama3.2

# 또는 더 큰 모델 (더 좋은 성능, 더 많은 메모리 필요)
ollama pull llama3.1:8b

# 또는 한국어 특화 모델
ollama pull qwen2.5:7b
```

사용 가능한 모델 목록 확인:

```bash
ollama list
```

## 🚀 설치 방법

1. 프로젝트 디렉토리로 이동:

```bash
cd pdf-rag-chatbot
```

2. 가상 환경 생성 (선택사항, 권장):

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

3. 필요한 패키지 설치:

```bash
pip install -r requirements.txt
```

**⚠️ Windows 사용자 주의사항:**

`tokenizers` 패키지 설치 시 Rust 관련 오류가 발생할 수 있습니다. 해결 방법:

1. **먼저 pip 업그레이드:**
```powershell
python -m pip install --upgrade pip setuptools wheel
```

2. **다시 설치 시도:**
```powershell
pip install -r requirements.txt
```

여전히 문제가 발생하면 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)의 "Windows에서 tokenizers 설치 오류 해결" 섹션을 참고하세요.

## 💻 사용 방법

### 1. PDF 파일 준비

`pdfs` 디렉토리에 PDF 파일을 넣어주세요:

```bash
# PDF 파일들을 pdfs 디렉토리에 복사
mkdir pdfs
copy "your_file.pdf" pdfs\  # Windows
# 또는
cp "your_file.pdf" pdfs/    # macOS/Linux
```

### 2. 웹 서버 실행 (권장)

FastAPI 웹 서버를 실행하여 웹 인터페이스와 API를 사용할 수 있습니다:

```bash
python app.py
```

서버가 실행되면 다음 URL로 접근할 수 있습니다:

- **웹 인터페이스**: `http://localhost:8000/static/index.html`
- **API 문서 (Swagger)**: `http://localhost:8000/api/docs`
- **API 문서 (ReDoc)**: `http://localhost:8000/api/redoc`
- **서버 상태 확인**: `http://localhost:8000/`
- **헬스 체크**: `http://localhost:8000/api/health`

### 3. CLI 모드 실행 (선택사항)

콘솔에서 직접 사용하려면:

```bash
python rag_chatbot_ollama.py
```

챗봇이 실행되면 질문을 입력할 수 있습니다:

- 질문을 입력하면 PDF 문서 기반으로 답변을 생성합니다
- 종료하려면 'quit', 'exit', 'q', 또는 '종료'를 입력하세요

### 4. 환경 변수 설정 (선택사항)

`.env` 파일을 생성하여 설정을 변경할 수 있습니다:

```env
# Ollama 서버 URL (기본값: http://localhost:11434)
OLLAMA_BASE_URL=http://localhost:11434

# 사용할 Ollama 모델 이름 (기본값: llama3.2)
OLLAMA_MODEL=llama3.2
```

## 📝 코드 사용 예시

```python
from rag_chatbot_ollama import RAGChatbot

# 챗봇 초기화 (PDF 파일은 pdfs 디렉토리에 있어야 함)
chatbot = RAGChatbot(
    pdf_directory="pdfs",
    model_name="llama3.2"  # 사용할 Ollama 모델 이름
)

# 질문하기
answer = chatbot.query("이 문서의 주요 내용은 무엇인가요?")
print(answer)

# 추가 PDF 파일 인덱싱
chatbot.ingest_pdfs("additional_pdfs")

# 대화형 채팅
response = chatbot.chat("이전 질문에 대해 더 자세히 설명해주세요")
print(response)
```

## 📁 프로젝트 구조

```
pdf-rag-chatbot/
├── rag_chatbot_ollama.py  # 메인 챗봇 코드 (Ollama 사용)
├── rag_chatbot.py         # OpenAI 사용 버전 (참고용)
├── requirements.txt       # 필요한 패키지 목록
├── .env                  # 환경 변수 (선택사항, 직접 생성)
├── README.md             # 프로젝트 설명서
├── pdfs/                 # PDF 파일 디렉토리
│   └── 본사 근무 가이드북 (1).pdf
└── chroma_db/            # ChromaDB 데이터 저장 디렉토리 (자동 생성)
```

## 🔧 주요 클래스 및 메서드

### RAGChatbot 클래스

- `__init__(pdf_directory, persist_dir, model_name)`: 챗봇 초기화
  - `pdf_directory`: PDF 파일이 있는 디렉토리 경로 (기본값: "pdfs")
  - `persist_dir`: ChromaDB 데이터 저장 디렉토리 (기본값: "./chroma_db")
  - `model_name`: 사용할 Ollama 모델 이름 (기본값: "llama3.2")
- `query(question, similarity_top_k)`: 질문에 대한 답변 생성
  - `question`: 사용자 질문
  - `similarity_top_k`: 유사한 문서를 몇 개까지 검색할지 (기본값: 5)
- `chat(question, chat_history)`: 대화형 채팅 인터페이스
  - `question`: 사용자 질문
  - `chat_history`: 이전 대화 기록 (선택사항)
- `ingest_pdfs(pdf_directory)`: 추가 PDF 파일 인덱싱

## ⚠️ 주의사항

- Ollama 서버가 실행 중이어야 합니다
- 첫 실행 시 embedding 모델 다운로드에 시간이 걸릴 수 있습니다 (약 400MB)
- PDF 파일은 `pdfs` 디렉토리에 있어야 합니다
- ChromaDB 데이터는 `chroma_db` 디렉토리에 저장됩니다
- 첫 실행 시 인덱스 생성에 시간이 걸릴 수 있습니다 (PDF 크기에 따라)

## 🐛 문제 해결

### Ollama 연결 오류

```
❌ Ollama 연결 실패: Connection refused
```

**해결 방법:**

1. Ollama가 설치되어 있는지 확인: `ollama --version`
2. Ollama 서버 실행: `ollama serve`
3. 모델이 다운로드되었는지 확인: `ollama list`
4. 모델이 없으면 다운로드: `ollama pull llama3.2`

### Embedding 모델 다운로드 오류

첫 실행 시 embedding 모델을 다운로드하는데 시간이 걸립니다. 네트워크 연결을 확인하세요.

### 메모리 부족 오류

더 작은 모델을 사용하거나, GPU가 있다면 `.env` 파일에서 device를 "cuda"로 설정하세요:

```python
# 코드에서 device="cuda"로 변경 (GPU 사용)
```

## 📚 추천 Ollama 모델

- **llama3.2** (2B): 빠르고 가벼움, 한국어 지원 양호
- **llama3.1:8b**: 더 좋은 성능, 더 많은 메모리 필요
- **qwen2.5:7b**: 한국어에 특화된 모델

모델 비교 및 다운로드:

```bash
ollama list              # 설치된 모델 목록
ollama pull llama3.2     # 모델 다운로드
ollama show llama3.2     # 모델 정보 확인
```

## 📄 라이선스

MIT
