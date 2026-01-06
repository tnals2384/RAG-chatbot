import type {
  ChatRequest,
  ChatResponse,
  QueryRequest,
  QueryResponse,
  ErrorResponse,
  HealthResponse,
  ResetSessionResponse,
} from "@/types/api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
    } as ChatRequest),
  });

  if (!response.ok) {
    const error: ErrorResponse = await response.json();
    throw new Error(error.message || "채팅 요청 실패");
  }

  return response.json();
}

export async function resetChatSession(
  sessionId: string
): Promise<ResetSessionResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/chat/session/${sessionId}`,
    {
      method: "DELETE",
    }
  );

  if (!response.ok) {
    const error: ErrorResponse = await response.json();
    throw new Error(error.message || "세션 초기화 실패");
  }

  return response.json();
}

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`);
    const data: HealthResponse = await response.json();
    return data.status === "healthy" && data.chatbot_initialized;
  } catch {
    return false;
  }
}

export async function sendQuery(
  question: string,
  similarityTopK: number = 5
): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      similarity_top_k: similarityTopK,
    } as QueryRequest),
  });

  if (!response.ok) {
    const error: ErrorResponse = await response.json();
    throw new Error(error.message || "질문 처리 실패");
  }

  return response.json();
}

