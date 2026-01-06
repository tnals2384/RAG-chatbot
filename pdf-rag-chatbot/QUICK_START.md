# 빠른 시작 가이드

## 404 에러 해결하기

### 1단계: 서버 실행 확인

터미널에서 다음 명령어로 서버를 실행하세요:

```bash
python app.py
```

서버가 정상적으로 실행되면 다음과 같은 메시지가 표시됩니다:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
============================================================
🚀 서버 시작 중... 챗봇을 자동으로 초기화합니다.
============================================================
```

### 2단계: 브라우저에서 테스트

서버가 실행 중일 때, 브라우저에서 다음 URL을 열어보세요:

1. **서버 상태 확인**
   ```
   http://localhost:8000/
   ```
   → JSON 응답이 보이면 서버가 정상 작동 중입니다.

2. **헬스 체크**
   ```
   http://localhost:8000/api/health
   ```
   → 서버 상태를 확인할 수 있습니다.

3. **API 문서 (Swagger)**
   ```
   http://localhost:8000/api/docs
   ```
   → 여기서 모든 API를 테스트할 수 있습니다.

### 3단계: 올바른 엔드포인트 사용

**✅ 올바른 엔드포인트:**
- `POST http://localhost:8000/api/chat`
- `GET http://localhost:8000/api/health`
- `POST http://localhost:8000/api/query`

**❌ 잘못된 엔드포인트:**
- `http://localhost:8000/chat` (앞에 `/api`가 없음)
- `http://localhost:8000/api/chat/` (끝에 `/`가 있음)
- `http://localhost:8000/static/chat` (잘못된 경로)

### 4단계: Next.js에서 호출 시

```typescript
// ✅ 올바른 방법
const response = await fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    question: '질문 내용',
    session_id: 'session_123'
  })
});

// ❌ 잘못된 방법
const response = await fetch('/api/chat', { ... }); // 상대 경로는 안 됨
const response = await fetch('http://localhost:8000/chat', { ... }); // /api 없음
```

### 5단계: 문제 해결 체크리스트

- [ ] 서버가 실행 중인가요? (`python app.py`)
- [ ] 포트가 8000번인가요?
- [ ] URL에 `/api` prefix가 있나요?
- [ ] HTTP 메서드가 맞나요? (`POST`, `GET`, `DELETE`)
- [ ] Content-Type 헤더가 `application/json`인가요?

### 6단계: curl로 테스트

터미널에서 직접 테스트해보세요:

```bash
# 헬스 체크
curl http://localhost:8000/api/health

# 채팅 테스트
curl -X POST http://localhost:8000/api/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"question\": \"안녕하세요\", \"session_id\": \"test\"}"
```

(Windows에서는 `^` 대신 백슬래시 `\`를 사용하거나 PowerShell을 사용하세요)

### 7단계: 서버 로그 확인

서버 콘솔에서 다음과 같은 로그를 확인하세요:

```
INFO:     127.0.0.1:xxxxx - "GET /api/health HTTP/1.1" 200 OK
```

404 에러가 발생하면:
```
INFO:     127.0.0.1:xxxxx - "GET /wrong/path HTTP/1.1" 404 Not Found
```

## 자주 발생하는 실수

1. **서버 미실행**: 가장 흔한 원인입니다. `python app.py` 실행 확인
2. **잘못된 URL**: `/api` prefix 누락
3. **포트 번호 누락**: `localhost/api/chat` → `localhost:8000/api/chat`
4. **서버 미재시작**: 코드 변경 후 서버 재시작 필요

## 여전히 해결되지 않으면

1. 브라우저 개발자 도구의 Network 탭 확인
2. 서버 콘솔의 에러 메시지 확인
3. `http://localhost:8000/api/docs`에서 Swagger UI로 직접 테스트

