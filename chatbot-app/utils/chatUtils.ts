/**
 * 세션 ID 생성
 */
export function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * 클립보드에 텍스트 복사
 */
export async function copyToClipboard(text: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(text);
  } catch (error) {
    console.error("복사 실패:", error);
    throw new Error("복사에 실패했습니다.");
  }
}

/**
 * 에러 메시지 포맷팅
 */
export function formatErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "알 수 없는 오류";
}
