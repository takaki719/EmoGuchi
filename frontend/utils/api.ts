export function getApiUrl(): string {
  // ビルド時の環境変数を優先
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  
  // ブラウザ環境での動的判定
  if (typeof window !== 'undefined') {
    // 本番環境の場合、同じオリジンのAPIを使用
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      // プロトコルとホスト名を維持し、ポート8000を使用
      return `${window.location.protocol}//${window.location.hostname}:8000`;
    }
  }
  
  // 開発環境のデフォルト
  return 'http://localhost:8000';
}