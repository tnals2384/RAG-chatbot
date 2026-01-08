"use client";

import { useState, useEffect, useCallback } from "react";
import { useSession } from "next-auth/react";
import {
  getChatHistories,
  deleteChatHistory,
} from "@/lib/api";
import type { Chat } from "@/types/auth";

interface ChatSidebarProps {
  onSelectChat: (chatId: string) => void;
  currentChatId: string | null;
  onNewChat: () => void;
  onChatListUpdate?: () => void;
  refreshTrigger?: number; // 이 값이 변경되면 채팅 목록 새로고침
}

export default function ChatSidebar({
  onSelectChat,
  currentChatId,
  onNewChat,
  onChatListUpdate,
  refreshTrigger,
}: ChatSidebarProps) {
  const { data: session } = useSession();
  const [chatHistories, setChatHistories] = useState<Omit<Chat, "userId">[]>([]);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(true);

  const loadChatHistories = useCallback(async () => {
    if (!session?.user?.id) return;
    setLoading(true);
    try {
      // getChatHistories는 Omit<Chat, "userId">[] 타입을 반환
      // 백엔드 응답 { success: true, chats: [...] }에서 chats 배열을 추출
      const histories = await getChatHistories(session.user.id);
      setChatHistories(histories);
    } catch (error) {
      console.error("채팅 기록 로드 실패:", error);
      setChatHistories([]);
    } finally {
      setLoading(false);
    }
  }, [session?.user?.id]);

  useEffect(() => {
    if (session?.user?.id) {
      loadChatHistories();
    }
  }, [session?.user?.id, loadChatHistories]);

  // refreshTrigger가 변경되면 채팅 목록 새로고침
  useEffect(() => {
    if (session?.user?.id && refreshTrigger !== undefined) {
      loadChatHistories();
    }
  }, [refreshTrigger, session?.user?.id, loadChatHistories]);

  const handleDelete = async (chatId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!session?.user?.id) return;
    if (!confirm("이 대화를 삭제하시겠습니까?")) return;

    try {
      await deleteChatHistory(chatId, session.user.id);
      setChatHistories((prev) => prev.filter((chat) => chat.id !== chatId));
      if (currentChatId === chatId) {
        onNewChat();
      }
      if (onChatListUpdate) {
        onChatListUpdate();
      }
    } catch (error) {
      console.error("채팅 기록 삭제 실패:", error);
      alert("삭제에 실패했습니다.");
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return "오늘";
    if (days === 1) return "어제";
    if (days < 7) return `${days}일 전`;
    return date.toLocaleDateString("ko-KR");
  };

  if (!session) {
    return null;
  }

  return (
    <>
      {/* 모바일 오버레이 */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* 사이드바 */}
      <div
        className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col transition-transform duration-300 ${
          isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        }`}
      >
        {/* 헤더 */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-800">
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={onNewChat}
              className="w-full rounded-lg bg-pink-500 hover:bg-pink-600 text-white px-4 py-2 text-sm font-medium transition-colors"
            >
              + 새 대화
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="lg:hidden ml-2 p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-800"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
                className="w-5 h-5"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
          <div className="flex items-center gap-2">
            {session.user?.image && (
              <img
                src={session.user.image}
                alt={session.user.name || ""}
                className="w-8 h-8 rounded-full"
              />
            )}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                {session.user?.name}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                {session.user?.email}
              </p>
            </div>
          </div>
        </div>

        {/* 채팅 목록 */}
        <div className="flex-1 overflow-y-auto p-2">
          {loading ? (
            <div className="text-center text-gray-500 dark:text-gray-400 py-8">
              로딩 중...
            </div>
          ) : chatHistories.length === 0 ? (
            <div className="text-center text-gray-500 dark:text-gray-400 py-8">
              대화 기록이 없습니다
            </div>
          ) : (
            <div className="space-y-1">
              {chatHistories.map((chat) => (
                <div
                  key={chat.id}
                  onClick={() => {
                    onSelectChat(chat.id);
                    setIsOpen(false);
                  }}
                  className={`group relative p-3 rounded-lg cursor-pointer transition-colors ${
                    currentChatId === chat.id
                      ? "bg-pink-100 dark:bg-pink-900/30"
                      : "hover:bg-gray-200 dark:hover:bg-gray-800"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                        {chat.title || "제목 없음"}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {formatDate(chat.updatedAt)}
                      </p>
                    </div>
                    <button
                      onClick={(e) => handleDelete(chat.id, e)}
                      className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-gray-300 dark:hover:bg-gray-700 transition-opacity"
                      title="삭제"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth={1.5}
                        stroke="currentColor"
                        className="w-4 h-4 text-gray-500 dark:text-gray-400"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"
                        />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 모바일 메뉴 버튼 */}
      <button
        onClick={() => setIsOpen(true)}
        className="lg:hidden fixed bottom-4 left-4 z-30 p-3 bg-pink-500 hover:bg-pink-600 text-white rounded-full shadow-lg"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
          className="w-6 h-6"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
          />
        </svg>
      </button>
    </>
  );
}
