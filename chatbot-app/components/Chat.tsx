"use client";

import { useChat } from "@/hooks/useChat";
import { copyToClipboard } from "@/utils/chatUtils";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useSession, signIn, signOut } from "next-auth/react";
import ChatSidebar from "./ChatSidebar";

export default function Chat() {
  const { data: session } = useSession();
  const [input, setInput] = useState("");
  const [copiedMessageId, setCopiedMessageId] = useState<number | null>(null);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [sidebarRefreshTrigger, setSidebarRefreshTrigger] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const {
    messages,
    loading,
    isLoadingHistory,
    sendMessage,
    resendMessage,
    resetSession,
    startNewChat,
    loadChatHistory,
  } = useChat({
    chatId: currentChatId,
    onChatIdChange: setCurrentChatId,
    onChatSaved: () => {
      // 채팅 저장 후 사이드바 새로고침 트리거
      setSidebarRefreshTrigger((prev) => prev + 1);
    },
  });

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
    await sendMessage(userMessage);
  };

  const handleReset = async () => {
    try {
      await resetSession();
    } catch (error) {
      alert(
        error instanceof Error ? error.message : "세션 초기화에 실패했습니다."
      );
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleCopy = async (content: string, messageIndex: number) => {
    try {
      await copyToClipboard(content);
      setCopiedMessageId(messageIndex);
      setTimeout(() => {
        setCopiedMessageId(null);
      }, 2000);
    } catch (error) {
      alert(error instanceof Error ? error.message : "복사에 실패했습니다.");
    }
  };

  const handleResend = async (content: string, messageIndex: number) => {
    await resendMessage(content, messageIndex);
  };

  return (
    <div className="flex h-screen bg-white dark:bg-gray-900">
      {/* 사이드바 - 로그인한 사용자에게만 표시 */}
      {session && (
        <ChatSidebar
          onSelectChat={(chatId) => {
            setCurrentChatId(chatId);
            loadChatHistory(chatId);
          }}
          currentChatId={currentChatId}
          onNewChat={() => {  
            startNewChat();
          }}
          refreshTrigger={sidebarRefreshTrigger}
        />
      )}

      {/* 메인 콘텐츠 */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* 헤더 */}
        <div className="border-b border-gray-200 bg-white px-4 py-3 dark:border-gray-700 dark:bg-gray-800">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-semibold bg-gradient-to-r from-pink-600 to-pink-400 bg-clip-text text-transparent dark:from-pink-400 dark:to-pink-300">
              헤이플
            </h1>
            <div className="flex items-center gap-3">
              {/* 로그인하지 않은 경우에만 대화 초기화 버튼 표시 */}
              {!session && (
                <button
                  onClick={handleReset}
                  disabled={loading || messages.length === 0}
                  className="cursor-pointer rounded-lg bg-pink-400 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-pink-500 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-pink-600 dark:hover:bg-pink-700"
                >
                  대화 초기화
                </button>
              )}
              {session ? (
                <button
                  onClick={() => signOut()}
                  className="cursor-pointer rounded-lg border border-gray-300 dark:border-gray-700 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  로그아웃
                </button>
              ) : (
                <button
                  onClick={() => signIn("google")}
                  className="cursor-pointer rounded-lg bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex items-center gap-2"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    className="w-4 h-4"
                  >
                    <path
                      fill="#4285F4"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="#34A853"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="#FBBC05"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    />
                    <path
                      fill="#EA4335"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    />
                  </svg>
                  로그인
                </button>
              )}
            </div>
          </div>
        </div>

        {/* 메시지 영역 */}
        <div className="flex-1 overflow-y-auto px-4 py-6 bg-white dark:bg-gray-900">
          <div className="mx-auto max-w-4xl space-y-4">
            {isLoadingHistory ? (
              <div className="flex h-full items-center justify-center">
                <div className="text-center">
                  <p className="text-lg text-gray-500 dark:text-gray-400">
                    채팅 기록을 불러오는 중...
                  </p>
                </div>
              </div>
            ) : messages.length === 0 ? (
              <div className="flex h-full items-center justify-center">
                <div className="text-center">
                  <p className="text-lg text-gray-500 dark:text-gray-400">
                    안녕하세요! 질문을 입력해주세요.
                  </p>
                </div>
              </div>
            ) : null}
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`group flex items-start gap-2 ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {/* 액션 버튼들 - 말풍선 왼쪽 (사용자 메시지만) */}
              {!msg.isLoading && msg.role === "user" && (
                <div className="flex gap-1 opacity-0 transition-opacity group-hover:opacity-100 order-1">
                  <button
                    onClick={() => handleResend(msg.content, idx)}
                    disabled={loading}
                    className="rounded-md bg-white/90 backdrop-blur-sm p-1.5 text-pink-600 shadow-sm transition-all hover:bg-white hover:shadow-md disabled:cursor-not-allowed disabled:opacity-50 dark:bg-gray-700/90 dark:text-pink-400 dark:hover:bg-gray-700"
                    title="다시 보내기"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      strokeWidth={1.5}
                      stroke="currentColor"
                      className="h-3.5 w-3.5"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99"
                      />
                    </svg>
                  </button>
                  <button
                    onClick={() => handleCopy(msg.content, idx)}
                    className={`rounded-md p-1.5 shadow-sm transition-all backdrop-blur-sm ${
                      copiedMessageId === idx
                        ? "bg-green-100 text-green-600 dark:bg-green-900/90 dark:text-green-300"
                        : "bg-white/90 text-pink-600 hover:bg-white hover:shadow-md dark:bg-gray-700/90 dark:text-pink-400 dark:hover:bg-gray-700"
                    }`}
                    title={copiedMessageId === idx ? "복사됨!" : "복사"}
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      strokeWidth={1.5}
                      stroke="currentColor"
                      className="h-3.5 w-3.5"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M15.666 3.888A2.25 2.25 0 0 0 13.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 0 1-.75.75H9a.75.75 0 0 1-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 0 1-2.25 2.25H6.75A2.25 2.25 0 0 1 4.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 0 1 1.927-.184m1.5-2.828A48.208 48.208 0 0 0 8.25 2.5H5.625a2.25 2.25 0 0 0-1.907 1.638M5.625 6h4.125m-4.125 0v.375m0 11.25v-9m0 9h-4.125m4.125 0h4.125"
                      />
                    </svg>
                  </button>
                </div>
              )}
              
              <div
                className={`max-w-[80%] rounded-lg px-4 py-3 order-2 ${
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
              
              {/* 봇 말풍선 오른쪽 복사 버튼 */}
              {!msg.isLoading && msg.role === "bot" && (
                <div className="flex gap-1 opacity-0 transition-opacity group-hover:opacity-100 order-3">
                  <button
                    onClick={() => handleCopy(msg.content, idx)}
                    className={`rounded-md p-1.5 shadow-sm transition-all backdrop-blur-sm ${
                      copiedMessageId === idx
                        ? "bg-green-100 text-green-600 dark:bg-green-900/90 dark:text-green-300"
                        : "bg-white/90 text-pink-600 hover:bg-white hover:shadow-md dark:bg-gray-700/90 dark:text-pink-400 dark:hover:bg-gray-700"
                    }`}
                    title={copiedMessageId === idx ? "복사됨!" : "복사"}
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      strokeWidth={1.5}
                      stroke="currentColor"
                      className="h-3.5 w-3.5"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M15.666 3.888A2.25 2.25 0 0 0 13.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 0 1-.75.75H9a.75.75 0 0 1-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 0 1-2.25 2.25H6.75A2.25 2.25 0 0 1 4.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 0 1 1.927-.184m1.5-2.828A48.208 48.208 0 0 0 8.25 2.5H5.625a2.25 2.25 0 0 0-1.907 1.638M5.625 6h4.125m-4.125 0v.375m0 11.25v-9m0 9h-4.125m4.125 0h4.125"
                      />
                    </svg>
                  </button>
                </div>
              )}
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
                disabled={loading || isLoadingHistory}
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
                disabled={loading || !input.trim() || isLoadingHistory}
                className="cursor-pointer rounded-lg bg-gradient-to-r from-pink-400 to-pink-500 px-6 py-3 font-medium text-white transition-all hover:from-pink-500 hover:to-pink-600 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-50 dark:from-pink-600 dark:to-pink-700 dark:hover:from-pink-700 dark:hover:to-pink-800"
              >
                {loading ? "전송 중..." : "전송"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
