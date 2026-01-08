import type {
  ChatRequest,
  ChatResponse,
  QueryRequest,
  QueryResponse,
  ErrorResponse,
  HealthResponse,
  ResetSessionResponse,
} from "@/types/api";
import type { Chat, ChatHistory, Message } from "@/types/auth";

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

/**
 * 채팅 기록 저장
 * SQL 스키마:
 * - chats 테이블에 채팅방 정보 저장 (id, title, user_id, created_at, updated_at)
 * - messages 테이블에 메시지들 저장 (id, chat_id, role, content, created_at)
 * 
 * 백엔드 응답 형식: { success: true, message: "...", chat: {...} }
 */
export async function saveChatHistory(
  userId: string,
  title: string,
  messages: Message[],
  chatId?: string
): Promise<{ success: boolean; chatId: string }> {
  const response = await fetch(`${API_BASE_URL}/api/chats`, {
    method: chatId ? "PUT" : "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      userId,
      title,
      messages: messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
        // id, chatId, createdAt은 서버에서 처리
      })),
      chatId,
    }),
  });

  if (!response.ok) {
    const error: ErrorResponse = await response.json();
    throw new Error(error.message || "채팅 기록 저장 실패");
  }

  const data = await response.json();
  // 백엔드가 { success: true, chat: {...} } 형태로 반환하므로 chat.id를 chatId로 변환
  if (data && data.chat && data.chat.id) {
    return {
      success: data.success || true,
      chatId: data.chat.id,
    };
  }
  
  // 예상치 못한 응답 형식
  throw new Error("예상치 못한 API 응답 형식: chat 필드가 없습니다.");
}

/**
 * 사용자의 채팅 기록 목록 조회
 * SQL: SELECT id, title, created_at, updated_at FROM chats WHERE user_id = ?
 * ORDER BY updated_at DESC
 * 
 * 백엔드 응답 형식: { success: true, message: "...", chats: [...] }
 */
export async function getChatHistories(userId: string): Promise<Omit<Chat, "userId">[]> {
  const response = await fetch(`${API_BASE_URL}/api/chats?userId=${userId}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const error: ErrorResponse = await response.json();
    throw new Error(error.message || "채팅 기록 조회 실패");
  }

  const data = await response.json();
  // 백엔드가 { success: true, chats: [...] } 형태로 반환하므로 chats 배열 추출
  // 각 chat은 ChatHistory 타입이지만 messages는 빈 배열이므로 Omit<Chat, "userId">로 변환
  if (data && Array.isArray(data.chats)) {
    return data.chats.map((chat: ChatHistory) => ({
      id: chat.id,
      title: chat.title,
      createdAt: chat.createdAt,
      updatedAt: chat.updatedAt,
    }));
  }
  
  // 예상치 못한 응답 형식
  console.error("예상치 못한 API 응답 형식:", data);
  return [];
}

/**
 * 특정 채팅 기록 조회
 * SQL: 
 *   SELECT c.id, c.title, c.user_id, c.created_at, c.updated_at
 *   FROM chats c WHERE c.id = ? AND c.user_id = ?
 *   
 *   SELECT m.id, m.chat_id, m.role, m.content, m.created_at
 *   FROM messages m WHERE m.chat_id = ? ORDER BY m.created_at ASC
 * 
 * 백엔드 응답 형식: { success: true, message: "...", chat: {...} }
 */
export async function getChatHistory(
  chatId: string,
  userId: string
): Promise<ChatHistory> {
  const response = await fetch(
    `${API_BASE_URL}/api/chats/${chatId}?userId=${userId}`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    const error: ErrorResponse = await response.json();
    throw new Error(error.message || "채팅 기록 조회 실패");
  }

  const data = await response.json();
  // 백엔드가 { success: true, chat: {...} } 형태로 반환하므로 chat 객체 추출
  if (data && data.chat) {
    return data.chat;
  }
  
  // 예상치 못한 응답 형식
  throw new Error("예상치 못한 API 응답 형식: chat 필드가 없습니다.");
}

/**
 * 채팅 기록 삭제
 */
export async function deleteChatHistory(
  chatId: string,
  userId: string
): Promise<{ success: boolean }> {
  const response = await fetch(
    `${API_BASE_URL}/api/chats/${chatId}?userId=${userId}`,
    {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    const error: ErrorResponse = await response.json();
    throw new Error(error.message || "채팅 기록 삭제 실패");
  }

  return response.json();
}

