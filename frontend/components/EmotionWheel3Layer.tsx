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
        return { inner: middleRadius, outer: outerRadius };
      case 'medium':
        return { inner: innerRadius, outer: middleRadius };
      case 'weak':
        return { inner: centerRadius, outer: innerRadius };
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

  const getEmojiPosition = (emotion: PlutchikEmotion) => {
    const radii = getRadiusForIntensity(emotion.intensity);
    const emojiRadius = radii.outer * 0.85;
    const angle = emotion.angle * Math.PI / 180;
    const x = centerX + emojiRadius * Math.cos(angle);
    const y = centerY + emojiRadius * Math.sin(angle);
    return { x, y };
  };

  const handleEmotionClick = (emotionId: string) => {
    if (!disabled && onEmotionSelect) {
      onEmotionSelect(emotionId);
    }
  };

  const handleAxisHover = (emotion: PlutchikEmotion, event: React.MouseEvent) => {
    if (!disabled) {
      setHoveredAxis(emotion.axis);
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

  // Get font size based on intensity level
  const getFontSize = (intensity: IntensityLevel) => {
    switch (intensity) {
      case 'strong':
        return size * 0.025;
      case 'medium':
        return size * 0.028;
      case 'weak':
        return size * 0.032;
      default:
        return size * 0.028;
    }
  };

  const getEmojiFontSize = (intensity: IntensityLevel) => {
    switch (intensity) {
      case 'strong':
        return size * 0.045;
      case 'medium':
        return size * 0.05;
      case 'weak':
        return size * 0.055;
      default:
        return size * 0.05;
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
          const emojiPos = getEmojiPosition(emotion);
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
                    handleAxisHover(emotion, e);
                  }
                }}
                onMouseLeave={() => {
                  setHoveredEmotion(null);
                  handleAxisLeave();
                }}
                className={`${!disabled ? 'hover:opacity-95 transition-all duration-200' : ''}`}
              />
              
              {/* Text label - show for medium intensity or when selected/hovered */}
              {(emotion.intensity === 'medium' || selected || hovered) && (
                <text
                  x={textPos.x}
                  y={textPos.y}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fontSize={getFontSize(emotion.intensity)}
                  fontWeight={selected ? 'bold' : 'normal'}
                  fill={selected ? '#000' : hovered ? '#000' : '#333'}
                  stroke={selected || hovered ? '#fff' : 'none'}
                  strokeWidth={selected || hovered ? '0.5' : '0'}
                  pointerEvents="none"
                  className="select-none"
                  style={{
                    filter: selected || hovered ? 'drop-shadow(1px 1px 2px rgba(0,0,0,0.5))' : 'none'
                  }}
                >
                  {emotion.nameJa}
                </text>
              )}

              {/* Emoji - adjust size based on intensity */}
              <text
                x={emojiPos.x}
                y={emojiPos.y}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize={getEmojiFontSize(emotion.intensity)}
                pointerEvents="none"
                className="select-none"
              >
                {emotion.emoji}
              </text>

              {/* Intensity indicator - small text for strong/weak */}
              {emotion.intensity !== 'medium' && (
                <text
                  x={textPos.x}
                  y={textPos.y + getFontSize(emotion.intensity) * 0.8}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fontSize={getFontSize(emotion.intensity) * 0.7}
                  fontWeight={selected ? 'bold' : 'normal'}
                  fill={selected ? '#000' : '#555'}
                  pointerEvents="none"
                  className="select-none"
                >
                  {emotion.intensity === 'strong' ? '強' : '弱'}
                </text>
              )}
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
          <div className="font-semibold mb-1">
            {EMOTION_AXIS_INFO[hoveredAxis]?.nameJa}
          </div>
          <div className="text-xs mb-2">
            {EMOTION_AXIS_INFO[hoveredAxis]?.description}
          </div>
          <div className="text-xs text-gray-300">
            {EMOTION_AXIS_INFO[hoveredAxis]?.keywords.join('・')}
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="mt-4 text-xs text-gray-600 text-center">
        <div className="mb-1">内側から外側へ: 弱 → 中 → 強</div>
        <div>クリックして感情を選択・ホバーで軸の説明を表示</div>
      </div>
    </div>
  );
}

export { PLUTCHIK_EMOTIONS_3_LAYER };
export type { EmotionWheel3LayerProps, PlutchikEmotion, IntensityLevel };