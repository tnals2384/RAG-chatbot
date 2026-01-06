# 문제 해결 가이드

## 404 Not Found 에러 해결

### 1. 서버 실행 확인

먼저 FastAPI 서버가 실행 중인지 확인하세요:

```bash
# 서버 실행
python app.py

# 또는
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

서버가 정상적으로 실행되면 다음과 같은 메시지가 표시됩니다:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. 엔드포인트 확인

다음 URL들을 브라우저에서 직접 확인해보세요:

- `http://localhost:8000/` - 서버 상태 확인
- `http://localhost:8000/api/health` - 헬스 체크
- `http://localhost:8000/api/docs` - Swagger UI

### 3. 올바른 엔드포인트 사용

**올바른 엔드포인트:**
- ✅ `POST http://localhost:8000/api/chat`
- ✅ `GET http://localhost:8000/api/health`
- ✅ `POST http://localhost:8000/api/query`
- ✅ `DELETE http://localhost:8000/api/chat/session/{session_id}`

**잘못된 엔드포인트:**
- ❌ `http://localhost:8000/chat` (앞에 `/api`가 없음)
- ❌ `http://localhost:8000/api/chat/` (끝에 `/`가 있음)

### 4. Next.js에서 호출 시 확인사항

#### 환경 변수 설정

`.env.local` 파일 확인:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### API 호출 예시

```typescript
// 올바른 호출
const response = await fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    question: '질문',
    session_id: 'session_123'
  })
});

// 또는 환경 변수 사용
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const response = await fetch(`${API_URL}/api/chat`, { ... });
```

### 5. CORS 문제 해결

만약 CORS 에러가 발생한다면, `app.py`의 CORS 설정을 확인하세요:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경에서는 모든 origin 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 6. 서버 재시작

코드를 수정한 후에는 서버를 재시작해야 합니다:

```bash
# Ctrl+C로 서버 중지 후 다시 시작
python app.py
```

### 7. 포트 확인

다른 프로세스가 8000 포트를 사용 중일 수 있습니다:

```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

다른 포트를 사용하려면:
```python
uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)
```

### 8. 테스트 방법

#### curl로 테스트

```bash
# 헬스 체크
curl http://localhost:8000/api/health

# 채팅 테스트
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "안녕하세요", "session_id": "test_session"}'
```

#### 브라우저에서 테스트

1. `http://localhost:8000/api/docs` 접속
2. Swagger UI에서 직접 API 테스트 가능

### 9. 일반적인 실수

1. **URL 끝에 슬래시 추가**: `/api/chat/` ❌ → `/api/chat` ✅
2. **대소문자 구분**: `/api/Chat` ❌ → `/api/chat` ✅
3. **포트 번호 누락**: `localhost/api/chat` ❌ → `localhost:8000/api/chat` ✅
4. **프로토콜 누락**: `localhost:8000/api/chat` ❌ → `http://localhost:8000/api/chat` ✅

### 10. 로그 확인

서버 콘솔에서 에러 메시지를 확인하세요:

```
INFO:     127.0.0.1:xxxxx - "GET /api/health HTTP/1.1" 200 OK
```

404 에러가 발생하면:
```
INFO:     127.0.0.1:xxxxx - "GET /wrong/path HTTP/1.1" 404 Not Found
```

## 빠른 체크리스트

- [ ] 서버가 실행 중인가요? (`python app.py`)
- [ ] 올바른 URL을 사용하고 있나요? (`/api/chat`)
- [ ] 포트 번호가 맞나요? (`:8000`)
- [ ] HTTP 메서드가 맞나요? (`POST`, `GET`, `DELETE`)
- [ ] Content-Type 헤더가 설정되어 있나요? (`application/json`)
- [ ] 요청 본문이 올바른 형식인가요? (JSON)

## 추가 도움

여전히 문제가 해결되지 않으면:
1. 서버 로그를 확인하세요
2. 브라우저 개발자 도구의 Network 탭을 확인하세요
3. `http://localhost:8000/api/docs`에서 Swagger UI로 직접 테스트해보세요

