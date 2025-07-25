// Player ID永続化のためのユーティリティ

const PLAYER_ID_KEY = 'emoguchi_player_id';
const PLAYER_NAME_KEY = 'emoguchi_player_name';

/**
 * 保存されているPlayer IDを取得。なければ新規作成
 */
export function getOrCreatePlayerId(): string {
  if (typeof window === 'undefined') {
    // SSR時はランダムID返す
    return crypto.randomUUID();
  }

  let playerId = localStorage.getItem(PLAYER_ID_KEY);
  
  if (!playerId) {
    playerId = crypto.randomUUID();
    localStorage.setItem(PLAYER_ID_KEY, playerId);
  }
  
  return playerId;
}

/**
 * Player IDを取得（作成しない）
 */
export function getPlayerId(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }
  return localStorage.getItem(PLAYER_ID_KEY);
}

/**
 * Player名を保存
 */
export function savePlayerName(name: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(PLAYER_NAME_KEY, name);
}

/**
 * 保存されているPlayer名を取得
 */
export function getSavedPlayerName(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(PLAYER_NAME_KEY);
}

/**
 * Player情報をクリア（デバッグ用）
 */
export function clearPlayerInfo(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(PLAYER_ID_KEY);
  localStorage.removeItem(PLAYER_NAME_KEY);
}