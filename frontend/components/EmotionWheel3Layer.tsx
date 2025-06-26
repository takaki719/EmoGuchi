'use client';

import React, { useState } from 'react';
import { PLUTCHIK_EMOTIONS_3_LAYER, PlutchikEmotion, IntensityLevel } from '../types/plutchikEmotions';
import { EMOTION_AXIS_INFO } from '../types/emotionAxisInfo';

interface EmotionWheel3LayerProps {
  selectedEmotion?: string;
  onEmotionSelect?: (emotionId: string) => void;
  disabled?: boolean;
  size?: number;
}

export default function EmotionWheel3Layer({ 
  selectedEmotion, 
  onEmotionSelect, 
  disabled = false,
  size = 400 
}: EmotionWheel3LayerProps) {
  const [hoveredEmotion, setHoveredEmotion] = useState<string | null>(null);
  const [hoveredAxis, setHoveredAxis] = useState<string | null>(null);
  const [showTooltip, setShowTooltip] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  const centerX = size / 2;
  const centerY = size / 2;
  const outerRadius = size * 0.45;
  const middleRadius = size * 0.32;
  const innerRadius = size * 0.19;
  const centerRadius = size * 0.08;

  // Get radius for each intensity level
  const getRadiusForIntensity = (intensity: IntensityLevel): { inner: number; outer: number } => {
    switch (intensity) {
      case 'strong':
        return { inner: centerRadius, outer: innerRadius };
      case 'medium':
        return { inner: innerRadius, outer: middleRadius };
      case 'weak':
        return { inner: middleRadius, outer: outerRadius };
      default:
        return { inner: centerRadius, outer: innerRadius };
    }
  };

  const createSegmentPath = (emotion: PlutchikEmotion) => {
    const startAngle = (emotion.angle - 22.5) * Math.PI / 180;
    const endAngle = (emotion.angle + 22.5) * Math.PI / 180;
    const radii = getRadiusForIntensity(emotion.intensity);

    const x1 = centerX + radii.inner * Math.cos(startAngle);
    const y1 = centerY + radii.inner * Math.sin(startAngle);
    const x2 = centerX + radii.outer * Math.cos(startAngle);
    const y2 = centerY + radii.outer * Math.sin(startAngle);
    const x3 = centerX + radii.outer * Math.cos(endAngle);
    const y3 = centerY + radii.outer * Math.sin(endAngle);
    const x4 = centerX + radii.inner * Math.cos(endAngle);
    const y4 = centerY + radii.inner * Math.sin(endAngle);

    return `M ${x1} ${y1} L ${x2} ${y2} A ${radii.outer} ${radii.outer} 0 0 1 ${x3} ${y3} L ${x4} ${y4} A ${radii.inner} ${radii.inner} 0 0 0 ${x1} ${y1} Z`;
  };

  const getTextPosition = (emotion: PlutchikEmotion) => {
    const radii = getRadiusForIntensity(emotion.intensity);
    const textRadius = (radii.outer + radii.inner) / 2;
    const angle = emotion.angle * Math.PI / 180;
    const x = centerX + textRadius * Math.cos(angle);
    const y = centerY + textRadius * Math.sin(angle);
    return { x, y };
  };


  const handleEmotionClick = (emotionId: string) => {
    if (!disabled && onEmotionSelect) {
      onEmotionSelect(emotionId);
    }
  };

  const handleEmotionHover = (emotion: PlutchikEmotion, event: React.MouseEvent) => {
    if (!disabled) {
      setHoveredAxis(emotion.id); // Store emotion ID instead of axis
      setShowTooltip(true);
      setTooltipPosition({ x: event.clientX, y: event.clientY });
    }
  };

  const handleAxisLeave = () => {
    setHoveredAxis(null);
    setShowTooltip(false);
  };

  const isSelected = (emotionId: string) => selectedEmotion === emotionId;
  const isHovered = (emotionId: string) => hoveredEmotion === emotionId;

  // Get font size based on intensity level - larger fonts since no emojis
  const getFontSize = (intensity: IntensityLevel) => {
    switch (intensity) {
      case 'strong':
        return size * 0.035;
      case 'medium':
        return size * 0.035;
      case 'weak':
        return size * 0.030;
      default:
        return size * 0.035;
    }
  };


  const selectedEmotionData = selectedEmotion ? 
    PLUTCHIK_EMOTIONS_3_LAYER.find(e => e.id === selectedEmotion) : null;

  return (
    <div className="flex flex-col items-center">
      <svg 
        width={size} 
        height={size} 
        viewBox={`0 0 ${size} ${size}`}
        className={`${disabled ? 'opacity-50' : 'cursor-pointer'} max-w-full h-auto`}
      >
        <defs>
          <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="2" dy="2" stdDeviation="3" floodOpacity="0.3"/>
          </filter>
          <filter id="innerShadow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur in="SourceAlpha" stdDeviation="2"/>
            <feOffset dx="1" dy="1" result="offset"/>
            <feFlood floodColor="#000000" floodOpacity="0.2"/>
            <feComposite in2="offset" operator="in"/>
            <feMerge>
              <feMergeNode/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        {PLUTCHIK_EMOTIONS_3_LAYER.map((emotion) => {
          const textPos = getTextPosition(emotion);
          const selected = isSelected(emotion.id);
          const hovered = isHovered(emotion.id);

          return (
            <g key={emotion.id}>
              <path
                d={createSegmentPath(emotion)}
                fill={emotion.color}
                stroke={selected ? '#000' : '#fff'}
                strokeWidth={selected ? 2 : 0.5}
                opacity={selected ? 1 : hovered ? 0.9 : 0.8}
                filter={selected || hovered ? 'url(#shadow)' : 'url(#innerShadow)'}
                onClick={() => handleEmotionClick(emotion.id)}
                onMouseEnter={(e) => {
                  if (!disabled) {
                    setHoveredEmotion(emotion.id);
                    handleEmotionHover(emotion, e);
                  }
                }}
                onMouseLeave={() => {
                  setHoveredEmotion(null);
                  handleAxisLeave();
                }}
                className={`${!disabled ? 'hover:opacity-95 transition-all duration-200' : ''}`}
              />
              
              {/* Semi-transparent background box for text */}
              <rect
                x={textPos.x - getFontSize(emotion.intensity) * 1.2}
                y={textPos.y - getFontSize(emotion.intensity) * 0.4}
                width={getFontSize(emotion.intensity) * 2.4}
                height={getFontSize(emotion.intensity) * 0.8}
                fill="rgba(0, 0, 0, 0.4)"
                rx="3"
                ry="3"
                pointerEvents="none"
              />
              
              {/* Text label with white text and black shadow */}
              <text
                x={textPos.x}
                y={textPos.y}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize={getFontSize(emotion.intensity)}
                fontWeight="bold"
                fill="#fff"
                pointerEvents="none"
                className="select-none"
                style={{
                  filter: 'drop-shadow(0px 0px 3px rgba(0,0,0,0.8))'
                }}
              >
                {emotion.nameJa}
              </text>


            </g>
          );
        })}

        {/* Center circle with selected emotion or title */}
        <circle
          cx={centerX}
          cy={centerY}
          r={centerRadius}
          fill="#f8f9fa"
          stroke="#ddd"
          strokeWidth="1"
        />
        
        {selectedEmotionData ? (
          <>
            <text
              x={centerX}
              y={centerY - size * 0.025}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize={size * 0.025}
              fill="#333"
              fontWeight="bold"
              className="select-none"
            >
              {selectedEmotionData.nameJa}
            </text>
            <text
              x={centerX}
              y={centerY}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize={size * 0.02}
              fill="#666"
              className="select-none"
            >
              ({selectedEmotionData.nameEn})
            </text>
            <text
              x={centerX}
              y={centerY + size * 0.025}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize={size * 0.018}
              fill="#888"
              className="select-none"
            >
              {selectedEmotionData.intensity === 'strong' ? '強' : 
               selectedEmotionData.intensity === 'medium' ? '中' : '弱'}
            </text>
          </>
        ) : (
          <>
            <text
              x={centerX}
              y={centerY - size * 0.01}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize={size * 0.025}
              fill="#666"
              fontWeight="bold"
              className="select-none"
            >
              感情の輪
            </text>
            
            <text
              x={centerX}
              y={centerY + size * 0.02}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize={size * 0.02}
              fill="#888"
              className="select-none"
            >
              3層構造
            </text>
          </>
        )}

        {/* Layer boundaries */}
        <circle
          cx={centerX}
          cy={centerY}
          r={innerRadius}
          fill="none"
          stroke="#ddd"
          strokeWidth="1"
          opacity="0.5"
        />
        <circle
          cx={centerX}
          cy={centerY}
          r={middleRadius}
          fill="none"
          stroke="#ddd"
          strokeWidth="1"
          opacity="0.5"
        />
      </svg>

      {/* Tooltip */}
      {showTooltip && hoveredAxis && (
        <div 
          className="fixed z-50 bg-gray-800 text-white text-sm rounded-lg p-3 shadow-lg max-w-xs pointer-events-none"
          style={{
            left: tooltipPosition.x + 10,
            top: tooltipPosition.y - 10,
            transform: tooltipPosition.x > window.innerWidth - 200 ? 'translateX(-100%)' : 'none'
          }}
        >
          {(() => {
            const hoveredEmotion = PLUTCHIK_EMOTIONS_3_LAYER.find(e => e.id === hoveredAxis);
            if (!hoveredEmotion) return null;
            
            const intensityText = hoveredEmotion.intensity === 'strong' ? '強' : 
                                 hoveredEmotion.intensity === 'medium' ? '中' : '弱';
            
            return (
              <>
                <div className="font-semibold mb-1">
                  {hoveredEmotion.nameJa} ({hoveredEmotion.nameEn})
                </div>
                <div className="text-xs mb-1">
                  強度: {intensityText}
                </div>
                <div className="text-xs text-gray-300">
                  {hoveredEmotion.axis}軸の感情
                </div>
              </>
            );
          })()}
        </div>
      )}

      {/* Legend */}
      <div className="mt-4 text-xs text-gray-600 text-center">
        <div className="mb-1">内側から外側へ: 強 → 中 → 弱</div>
        <div>クリックして感情を選択・ホバーで感情の詳細を表示</div>
      </div>
    </div>
  );
}

export { PLUTCHIK_EMOTIONS_3_LAYER };
export type { EmotionWheel3LayerProps, PlutchikEmotion, IntensityLevel };