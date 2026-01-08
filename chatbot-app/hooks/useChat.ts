import { useState, useCallback, useEffect, useRef } from "react";
import { useSession } from "next-auth/react";
import {
  sendChatMessage,
  resetChatSession,
  saveChatHistory,
  getChatHistory,
} from "@/lib/api";
import type { Message } from "@/types/chat";
import { generateSessionId, formatErrorMessage } from "@/utils/chatUtils";

interface UseChatOptions {
  chatId?: string | null;
  onChatIdChange?: (chatId: string | null) => void;
  onChatSaved?: () => void; // 채팅 저장 후 호출되는 콜백
}

export function useChat(options?: UseChatOptions) {
  const { data: session } = useSession();
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => generateSessionId());
  const [currentChatId, setCurrentChatId] = useState<string | null>(
    options?.chatId || null
  );
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  // chatId가 변경되면 해당 채팅 기록 불러오기
  useEffect(() => {
    if (options?.chatId && session?.user?.id) {
      loadChatHistory(options.chatId);
    } else if (!options?.chatId) {
      setMessages([]);
      setCurrentChatId(null);
    }
  }, [options?.chatId, session?.user?.id]);

  // 채팅 기록 불러오기
  const loadChatHistory = async (chatId: string) => {
    if (!session?.user?.id) return;
    setIsLoadingHistory(true);
    try {
      const history = await getChatHistory(chatId, session.user.id);
      setMessages(
        history.messages.map((msg) => ({
          role: msg.role,
          content: msg.content,
          isLoading: false,
        }))
      );
      setCurrentChatId(chatId);
      if (options?.onChatIdChange) {
        options.onChatIdChange(chatId);
      }
    } catch (error) {
      console.error("채팅 기록 불러오기 실패:", error);
      alert("채팅 기록을 불러오는데 실패했습니다.");
    } finally {
      setIsLoadingHistory(false);
    }
  };

  // 채팅 기록 저장을 위한 ref
  const messagesRef = useRef<Message[]>([]);
  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  // 채팅 기록 저장
  const saveHistory = useCallback(
    async (title?: string) => {
      if (!session?.user?.id || messagesRef.current.length === 0) return;

      const chatTitle =
        title ||
        messagesRef.current
          .find((msg) => msg.role === "user")
          ?.content.substring(0, 30) || "새 대화";

      try {
        // 프론트엔드 Message 타입을 DB Message 타입으로 변환
        const dbMessages = messagesRef.current.map((msg) => ({
          role: msg.role,
          content: msg.content,
          // isLoading은 DB에 저장하지 않음
        }));
        const result = await saveChatHistory(
          session.user.id,
          chatTitle,
          dbMessages,
          currentChatId || undefined
        );
        setCurrentChatId(result.chatId);
        if (options?.onChatIdChange) {
          options.onChatIdChange(result.chatId);
        }
        // 채팅 저장 후 콜백 호출 (사이드바 새로고침용)
        if (options?.onChatSaved) {
          options.onChatSaved();
        }
      } catch (error) {
        console.error("채팅 기록 저장 실패:", error);
      }
    },
    [session?.user?.id, currentChatId, options]
  );

  /**
   * 로딩 메시지 생성
   */
  const createLoadingMessage = (): Message => ({
    role: "bot",
    content: "",
    isLoading: true,
  });

  /**
   * 메시지 전송
   */
  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || loading) return;

      const userMessage: Message = { role: "user", content: content.trim() };
      setMessages((prev) => [...prev, userMessage]);

      const loadingMessage = createLoadingMessage();
      setMessages((prev) => [...prev, loadingMessage]);
      setLoading(true);

      try {
        const response = await sendChatMessage(content.trim(), sessionId);
        setMessages((prev) => {
          const newMessages = [...prev];
          const loadingIndex = newMessages.findIndex(
            (msg) => msg.isLoading === true
          );
          if (loadingIndex !== -1) {
            newMessages[loadingIndex] = {
              role: "bot",
              content: response.answer,
              isLoading: false,
            };
          }
          return newMessages;
        });

        // 로그인한 사용자인 경우 채팅 기록 저장
        if (session?.user?.id) {
          // 약간의 지연 후 저장 (debounce 효과)
          setTimeout(() => {
            saveHistory();
          }, 1000);
        }
      } catch (error) {
        setMessages((prev) => {
          const newMessages = [...prev];
          const loadingIndex = newMessages.findIndex(
            (msg) => msg.isLoading === true
          );
          if (loadingIndex !== -1) {
            newMessages[loadingIndex] = {
              role: "bot",
              content: `오류: ${formatErrorMessage(error)}`,
              isLoading: false,
            };
          }
          return newMessages;
        });
      } finally {
        setLoading(false);
      }
    },
    [sessionId, loading, session?.user?.id, saveHistory]
  );

  /**
   * 메시지 재전송
   */
  const resendMessage = useCallback(
    async (content: string, messageIndex: number) => {
      if (loading) return;

      // 해당 메시지 이후의 모든 메시지 제거
      setMessages((prev) => prev.slice(0, messageIndex + 1));

      const loadingMessage = createLoadingMessage();
      setMessages((prev) => [...prev, loadingMessage]);
      setLoading(true);

      try {
        const response = await sendChatMessage(content, sessionId);
        setMessages((prev) => {
          const newMessages = [...prev];
          const loadingIndex = newMessages.findIndex(
            (msg) => msg.isLoading === true
          );
          if (loadingIndex !== -1) {
            newMessages[loadingIndex] = {
              role: "bot",
              content: response.answer,
              isLoading: false,
            };
          }
          return newMessages;
        });
      } catch (error) {
        setMessages((prev) => {
          const newMessages = [...prev];
          const loadingIndex = newMessages.findIndex(
            (msg) => msg.isLoading === true
          );
          if (loadingIndex !== -1) {
            newMessages[loadingIndex] = {
              role: "bot",
              content: `오류: ${formatErrorMessage(error)}`,
              isLoading: false,
            };
          }
          return newMessages;
        });
      } finally {
        setLoading(false);
      }
    },
    [sessionId, loading]
  );

  /**
   * 세션 초기화
   */
  const resetSession = useCallback(async () => {
    try {
      await resetChatSession(sessionId);
      setMessages([]);
      setCurrentChatId(null);
      if (options?.onChatIdChange) {
        options.onChatIdChange(null);
      }
    } catch (error) {
      console.error("세션 초기화 실패:", error);
      throw new Error(
        `세션 초기화 실패: ${formatErrorMessage(error)}`
      );
    }
  }, [sessionId, options]);

  /**
   * 새 채팅 시작
   */
  const startNewChat = useCallback(() => {
    setMessages([]);
    setCurrentChatId(null);
    if (options?.onChatIdChange) {
      options.onChatIdChange(null);
    }
  }, [options]);

  return {
    messages,
    loading,
    isLoadingHistory,
    sessionId,
    currentChatId,
    sendMessage,
    resendMessage,
    resetSession,
    startNewChat,
    loadChatHistory,
  };
}
