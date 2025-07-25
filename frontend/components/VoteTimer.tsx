'use client';

import { useEffect, useState } from 'react';

interface VoteTimerProps {
  startTime: string;          // ISO 8601 format
  timeoutSeconds: number;     // 制限時間（秒）
  onTimeout?: () => void;     // タイムアウト時のコールバック
}

export default function VoteTimer({ startTime, timeoutSeconds, onTimeout }: VoteTimerProps) {
  const [remainingSeconds, setRemainingSeconds] = useState(timeoutSeconds);
  const [percentage, setPercentage] = useState(100);
  const [isExpired, setIsExpired] = useState(false);

  useEffect(() => {
    const startTimestamp = new Date(startTime).getTime();
    
    const updateTimer = () => {
      const now = Date.now();
      const elapsed = (now - startTimestamp) / 1000; // 経過時間（秒）
      const remaining = Math.max(0, timeoutSeconds - elapsed);
      const percent = Math.max(0, (remaining / timeoutSeconds) * 100);
      
      setRemainingSeconds(Math.ceil(remaining));
      setPercentage(percent);
      
      if (remaining <= 0 && !isExpired) {
        setIsExpired(true);
        onTimeout?.();
      }
    };

    // 初回実行
    updateTimer();
    
    // 100msごとに更新（滑らかなアニメーション）
    const interval = setInterval(updateTimer, 100);
    
    return () => clearInterval(interval);
  }, [startTime, timeoutSeconds, onTimeout, isExpired]);

  // 色の決定（残り時間に応じて変化）
  const getBarColor = () => {
    if (percentage > 60) return 'bg-green-500';
    if (percentage > 30) return 'bg-yellow-500';
    if (percentage > 10) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getTextColor = () => {
    if (percentage > 60) return 'text-green-600';
    if (percentage > 30) return 'text-yellow-600';
    if (percentage > 10) return 'text-orange-600';
    return 'text-red-600';
  };

  if (isExpired) {
    return (
      <div className="w-full max-w-md mx-auto mb-4">
        <div className="text-center text-red-600 font-bold mb-2">
          ⏰ 投票時間終了
        </div>
        <div className="w-full bg-gray-200 rounded-full h-4">
          <div className="bg-red-500 h-4 rounded-full w-0 transition-all duration-300"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md mx-auto mb-4">
      <div className={`text-center ${getTextColor()} font-bold mb-2`}>
        投票残り時間: {remainingSeconds}秒
      </div>
      <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
        <div 
          className={`h-4 rounded-full transition-all duration-100 ease-linear ${getBarColor()}`}
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
      {percentage <= 10 && (
        <div className="text-center text-red-600 text-sm mt-1 animate-pulse">
          ⚠️ まもなく時間切れです！
        </div>
      )}
    </div>
  );
}