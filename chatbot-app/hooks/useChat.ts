import { useState, useCallback } from "react";
import { sendChatMessage, resetChatSession } from "@/lib/api";
import type { Message } from "@/types/chat";
import { generateSessionId, formatErrorMessage } from "@/utils/chatUtils";

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => generateSessionId());

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
    } catch (error) {
      console.error("세션 초기화 실패:", error);
      throw new Error(
        `세션 초기화 실패: ${formatErrorMessage(error)}`
      );
    }
  }, [sessionId]);

  return {
    messages,
    loading,
    sessionId,
    sendMessage,
    resendMessage,
    resetSession,
  };
}
