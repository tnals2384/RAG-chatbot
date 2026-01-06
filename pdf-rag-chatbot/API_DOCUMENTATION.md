# API 문서

Next.js 프론트엔드에서 사용하기 위한 RESTful API 문서입니다.

## 기본 정보

- **Base URL**: `http://localhost:8000`
- **API Prefix**: `/api`
- **Content-Type**: `application/json`

## 공통 응답 형식

### 성공 응답

```json
{
  "success": true,
  "message": "성공 메시지",
  "data": { ... }
}
```

### 에러 응답

```json
{
  "success": false,
  "message": "에러 메시지",
  "error": "ErrorCode",
  "detail": "상세 에러 정보"
}
```

## 엔드포인트 목록

### 1. 서버 상태 확인

#### `GET /`

서버 기본 상태 확인

**응답:**

```json
{
  "status": "running",
  "chatbot_initialized": true,
  "message": "PDF RAG 챗봇 API"
}
```

#### `GET /api/health`

헬스 체크

**응답:**

```json
{
  "status": "healthy",
  "chatbot_initialized": true,
  "message": "서버가 정상적으로 실행 중입니다."
}
```

---

### 2. 채팅 API

#### `POST /api/chat`

대화형 채팅 (대화 기록 유지)

**요청:**

```json
{
  "question": "사용자 질문",
  "session_id": "session_1234567890"
}
```

**응답:**

```json
{
  "success": true,
  "answer": "봇의 답변",
  "session_id": "session_1234567890",
  "message": "답변이 성공적으로 생성되었습니다."
}
```

**에러 응답 (503):**

```json
{
  "success": false,
  "message": "챗봇이 초기화되지 않았습니다.",
  "error": "ChatbotNotInitialized",
  "detail": "/api/init 엔드포인트를 먼저 호출하세요."
}
```

**사용 예시 (Next.js):**

```typescript
const response = await fetch("http://localhost:8000/api/chat", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    question: "연차는 어떻게 신청하나요?",
    session_id: "user_session_123",
  }),
});

const data = await response.json();
if (data.success) {
  console.log(data.answer);
} else {
  console.error(data.message);
}
```

---

#### `DELETE /api/chat/session/{session_id}`

특정 세션의 대화 기록 초기화

**경로 파라미터:**

- `session_id`: 초기화할 세션 ID

**응답:**

```json
{
  "success": true,
  "session_id": "session_1234567890",
  "message": "세션 'session_1234567890'의 대화 기록이 초기화되었습니다."
}
```

**사용 예시 (Next.js):**

```typescript
const response = await fetch(
  `http://localhost:8000/api/chat/session/${sessionId}`,
  {
    method: "DELETE",
  }
);

const data = await response.json();
```

---

#### `POST /api/chat/reset`

특정 세션의 대화 기록 초기화 (POST 메서드)

**요청:**

```json
{
  "session_id": "session_1234567890"
}
```

**응답:**

```json
{
  "success": true,
  "session_id": "session_1234567890",
  "message": "세션 'session_1234567890'의 대화 기록이 초기화되었습니다."
}
```

---

### 3. 질문 API

#### `POST /api/query`

단일 질문에 대한 답변 생성 (대화 기록 없음)

**요청:**

```json
{
  "question": "사용자 질문",
  "similarity_top_k": 5
}
```

**응답:**

```json
{
  "success": true,
  "answer": "봇의 답변",
  "message": "질문이 성공적으로 처리되었습니다."
}
```

**사용 예시 (Next.js):**

```typescript
const response = await fetch("http://localhost:8000/api/query", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    question: "연차는 어떻게 신청하나요?",
    similarity_top_k: 5,
  }),
});

const data = await response.json();
```

---

### 4. 초기화 API

#### `POST /api/init`

챗봇 초기화 (서버 시작 시 자동 초기화되지만 수동으로도 가능)

**요청:**

```json
{
  "pdf_directory": "pdfs",
  "persist_dir": "./chroma_db",
  "model_name": "qwen2.5:1.5b"
}
```

**응답:**

```json
{
  "success": true,
  "message": "챗봇 초기화가 완료되었습니다."
}
```

**에러 응답 (500):**

```json
{
  "success": false,
  "message": "챗봇 초기화에 실패했습니다.",
  "error": "InitializationError",
  "detail": "상세 에러 정보"
}
```

---

## Next.js 통합 예시

### TypeScript 타입 정의

```typescript
// types/api.ts

export interface ChatRequest {
  question: string;
  session_id?: string;
}

export interface ChatResponse {
  success: boolean;
  answer: string;
  session_id: string;
  message: string;
}

export interface ErrorResponse {
  success: false;
  message: string;
  error: string;
  detail?: string;
}
```

### API 클라이언트 함수

```typescript
// lib/api.ts

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function sendChatMessage(
  question: string,
  sessionId: string = "default"
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      session_id: sessionId,
    }),
  });

  if (!response.ok) {
    const error: ErrorResponse = await response.json();
    throw new Error(error.message || "채팅 요청 실패");
  }

  return response.json();
}

export async function resetChatSession(sessionId: string): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/chat/session/${sessionId}`,
    {
      method: "DELETE",
    }
  );

  if (!response.ok) {
    throw new Error("세션 초기화 실패");
  }
}

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`);
    const data = await response.json();
    return data.status === "healthy" && data.chatbot_initialized;
  } catch {
    return false;
  }
}
```

### React 컴포넌트 예시

```typescript
// components/Chat.tsx

"use client";

import { useState, useEffect } from "react";
import { sendChatMessage, resetChatSession } from "@/lib/api";

export default function Chat() {
  const [messages, setMessages] = useState<
    Array<{ role: "user" | "bot"; content: string }>
  >([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random()}`);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setLoading(true);

    try {
      const response = await sendChatMessage(userMessage, sessionId);
      setMessages((prev) => [
        ...prev,
        { role: "bot", content: response.answer },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          content: `오류: ${
            error instanceof Error ? error.message : "알 수 없는 오류"
          }`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    try {
      await resetChatSession(sessionId);
      setMessages([]);
    } catch (error) {
      console.error("세션 초기화 실패:", error);
    }
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
        {loading && <div className="message bot">답변 생성 중...</div>}
      </div>
      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === "Enter" && handleSend()}
          placeholder="질문을 입력하세요..."
        />
        <button onClick={handleSend} disabled={loading}>
          전송
        </button>
        <button onClick={handleReset}>초기화</button>
      </div>
    </div>
  );
}
```

---

## 환경 변수 설정

Next.js 프로젝트의 `.env.local` 파일:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 에러 코드

- `ChatbotNotInitialized`: 챗봇이 초기화되지 않음
- `QueryError`: 질문 처리 중 오류
- `ChatError`: 채팅 처리 중 오류
- `InitializationError`: 초기화 오류

---

## API 문서 확인

- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`
- OpenAPI JSON: `http://localhost:8000/api/openapi.json`
