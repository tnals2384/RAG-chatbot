"use client";

import { useState, useEffect, useRef } from "react";
import { sendChatMessage, resetChatSession } from "@/lib/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Message {
  role: "user" | "bot";
  content: string;
  isLoading?: boolean;
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(
    () => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  );
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput("");
    const newUserMessage: Message = { role: "user", content: userMessage };
    setMessages((prev) => [...prev, newUserMessage]);

    // 로딩 메시지 추가
    const loadingMessage: Message = {
      role: "bot",
      content: "",
      isLoading: true,
    };
    setMessages((prev) => [...prev, loadingMessage]);
    setLoading(true);

    try {
      const response = await sendChatMessage(userMessage, sessionId);
      // 로딩 메시지를 실제 답변으로 교체
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
      // 로딩 메시지를 에러 메시지로 교체
      setMessages((prev) => {
        const newMessages = [...prev];
        const loadingIndex = newMessages.findIndex(
          (msg) => msg.isLoading === true
        );
        if (loadingIndex !== -1) {
          newMessages[loadingIndex] = {
            role: "bot",
            content: `오류: ${
              error instanceof Error ? error.message : "알 수 없는 오류"
            }`,
            isLoading: false,
          };
        }
        return newMessages;
      });
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
      alert(
        `세션 초기화 실패: ${
          error instanceof Error ? error.message : "알 수 없는 오류"
        }`
      );
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-screen flex-col bg-white dark:bg-gray-900">
      {/* 헤더 */}
      <div className="border-b border-gray-200 bg-white px-4 py-3 dark:border-gray-700 dark:bg-gray-800">
        <div className="mx-auto flex max-w-4xl items-center justify-between">
          <h1 className="text-xl font-semibold bg-gradient-to-r from-pink-600 to-pink-400 bg-clip-text text-transparent dark:from-pink-400 dark:to-pink-300">
            헤이플
          </h1>
          <button
            onClick={handleReset}
            disabled={loading || messages.length === 0}
            className="rounded-lg bg-pink-400 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-pink-500 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-pink-600 dark:hover:bg-pink-700"
          >
            대화 초기화
          </button>
        </div>
      </div>

      {/* 메시지 영역 */}
      <div className="flex-1 overflow-y-auto px-4 py-6 bg-white dark:bg-gray-900">
        <div className="mx-auto max-w-4xl space-y-4">
          {messages.length === 0 && (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <p className="text-lg text-gray-500 dark:text-gray-400">
                  안녕하세요! 질문을 입력해주세요.
                </p>
              </div>
            </div>
          )}
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-3 ${
                  msg.role === "user"
                    ? "bg-gradient-to-r from-pink-200 to-pink-300 text-gray-800 shadow-md"
                    : "bg-white text-gray-900 shadow-sm dark:bg-gray-800 dark:text-gray-100 border border-pink-100 dark:border-pink-800"
                }`}
              >
                {msg.isLoading ? (
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 animate-bounce rounded-full bg-pink-400 [animation-delay:-0.3s]"></div>
                    <div className="h-2 w-2 animate-bounce rounded-full bg-pink-400 [animation-delay:-0.15s]"></div>
                    <div className="h-2 w-2 animate-bounce rounded-full bg-pink-400"></div>
                  </div>
                ) : msg.role === "bot" ? (
                  <div className="prose prose-sm max-w-none dark:prose-invert prose-headings:text-gray-900 dark:prose-headings:text-gray-100 prose-p:text-gray-800 dark:prose-p:text-gray-200 prose-strong:text-gray-900 dark:prose-strong:text-gray-100 prose-code:text-pink-600 dark:prose-code:text-pink-400 prose-pre:bg-gray-100 dark:prose-pre:bg-gray-800 prose-pre:text-gray-900 dark:prose-pre:text-gray-100">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <p className="whitespace-pre-wrap break-words">
                    {msg.content}
                  </p>
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* 입력 영역 */}
      <div className="border-t border-gray-200 bg-white px-4 py-4 dark:border-gray-700 dark:bg-gray-800">
        <div className="mx-auto max-w-4xl">
          <div className="flex gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="질문을 입력하세요... (Enter로 전송, Shift+Enter로 줄바꿈)"
              disabled={loading}
              rows={1}
              className="flex-1 resize-none rounded-lg border border-gray-300 px-4 py-3 text-gray-900 placeholder-gray-400 focus:border-pink-400 focus:outline-none focus:ring-2 focus:ring-pink-400 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder-gray-400 dark:focus:border-pink-500 dark:focus:ring-pink-500"
              style={{
                minHeight: "48px",
                maxHeight: "120px",
              }}
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement;
                target.style.height = "auto";
                target.style.height = `${Math.min(target.scrollHeight, 120)}px`;
              }}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="rounded-lg bg-gradient-to-r from-pink-400 to-pink-500 px-6 py-3 font-medium text-white transition-all hover:from-pink-500 hover:to-pink-600 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-50 dark:from-pink-600 dark:to-pink-700 dark:hover:from-pink-700 dark:hover:to-pink-800"
            >
              {loading ? "전송 중..." : "전송"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
