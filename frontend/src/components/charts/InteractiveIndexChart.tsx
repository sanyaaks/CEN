"use client";

import React, { useState } from "react";

interface DataPoint {
  label: string; // date, route, or horizon
  value: number; // index or fare
  secondaryValue?: number; // e.g. reference or min/max
  tooltipDetails?: string;
}

interface InteractiveIndexChartProps {
  data: DataPoint[];
  title?: string;
  valuePrefix?: string;
  valueSuffix?: string;
  height?: number;
  showReference?: boolean;
  baseLineValue?: number;
  accentColor?: "steel" | "navy" | "rose" | "gold" | "teal";
}

export default function InteractiveIndexChart({
  data,
  title,
  valuePrefix = "",
  valueSuffix = "",
  height = 300,
  baseLineValue = 100,
  accentColor = "steel"
}: InteractiveIndexChartProps) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  if (!data || data.length === 0) {
    return (
      <div className="h-56 flex flex-col items-center justify-center app-text-muted text-xs border app-border rounded-lg app-bg-card p-4 space-y-1">
        <span className="font-semibold app-text-primary">No Time-Series Observations</span>
        <span className="text-[11px]">Awaiting next automated index aggregation cycle</span>
      </div>
    );
  }

  const values = data.map((d) => d.value);
  const rawMin = Math.min(...values);
  const rawMax = Math.max(...values);

  // Symmetrical centering around baseline or data range
  let minVal: number;
  let maxVal: number;

  if (rawMax - rawMin < 1) {
    // If data is flat (e.g. all 100.0 baseline), center it nicely between 95 and 105
    const center = rawMin;
    minVal = center - 5;
    maxVal = center + 5;
  } else {
    const dataMin = baseLineValue !== undefined ? Math.min(rawMin, baseLineValue) : rawMin;
    const dataMax = baseLineValue !== undefined ? Math.max(rawMax, baseLineValue) : rawMax;
    const buffer = (dataMax - dataMin) * 0.18;
    minVal = Math.floor((dataMin - buffer) * 10) / 10;
    maxVal = Math.ceil((dataMax + buffer) * 10) / 10;
  }
  const range = maxVal - minVal || 1;

  const paddingLeft = 58;
  const paddingRight = 32;
  const paddingTop = 28;
  const paddingBottom = 36;
  const chartWidth = 820;
  const chartHeight = 320;

  const getX = (index: number) => {
    if (data.length <= 1) return (paddingLeft + chartWidth - paddingRight) / 2;
    return paddingLeft + (index / (data.length - 1)) * (chartWidth - paddingLeft - paddingRight);
  };

  const getY = (val: number) => {
    return (
      chartHeight -
      paddingBottom -
      ((val - minVal) / range) * (chartHeight - paddingTop - paddingBottom)
    );
  };

  // SVG coordinates
  const points = data.map((d, i) => `${getX(i)},${getY(d.value)}`).join(" ");

  const colorHex =
    accentColor === "steel"
      ? "#2E4A6B"
      : accentColor === "navy"
      ? "#1E2A44"
      : accentColor === "rose"
      ? "var(--color-rose)"
      : accentColor === "teal"
      ? "var(--color-teal)"
      : "#C29244";

  // Format label for display
  const formatLabel = (raw: string, index: number) => {
    if (!raw) return `Pt ${index + 1}`;
    if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) {
      const parts = raw.split("-");
      return `${parts[1]}/${parts[2]}`;
    }
    return raw;
  };

  const allDatesIdentical = data.length > 1 && data.every((d) => d.label === data[0].label);
  const midVal = (minVal + maxVal) / 2;

  return (
    <div className="w-full app-bg-card p-3.5 sm:p-5 rounded-lg border app-border space-y-3 shadow-sm transition-colors duration-200">
      {/* Header Info */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5 min-w-0">
        {title && (
          <h4 className="text-xs sm:text-sm font-bold app-text-heading tracking-wide truncate">
            {title}
          </h4>
        )}
        <div className="text-xs font-semibold flex items-center gap-2">
          {hoverIndex !== null && data[hoverIndex] ? (
            <span className="text-[var(--color-gold)] font-mono">
              {data[hoverIndex].label}:{" "}
              <strong className="app-text-primary">
                {valuePrefix}
                {data[hoverIndex].value.toFixed(2)}
                {valueSuffix}
              </strong>
            </span>
          ) : (
            <span className="app-text-muted font-mono text-[11px]">
              Latest:{" "}
              <strong className="app-text-primary">
                {valuePrefix}
                {data[data.length - 1].value.toFixed(2)}
                {valueSuffix}
              </strong>
            </span>
          )}
        </div>
      </div>

      {/* Chart SVG Container */}
      <div className="relative w-full h-[220px] sm:h-[260px] md:h-[290px] overflow-hidden select-none">
        <svg
          viewBox={`0 0 ${chartWidth} ${chartHeight}`}
          className="w-full h-full overflow-visible"
          preserveAspectRatio="none"
        >
          {/* Horizontal Grid Lines with Outside Y-Axis Values */}
          {[minVal, midVal, maxVal].map((val, idx) => {
            const yPos = getY(val);
            return (
              <g key={idx}>
                <line
                  x1={paddingLeft}
                  y1={yPos}
                  x2={chartWidth - paddingRight}
                  y2={yPos}
                  stroke="currentColor"
                  className="text-[var(--border-subtle)] opacity-60"
                  strokeDasharray="4 4"
                  strokeWidth="1"
                />
                <text
                  x={paddingLeft - 10}
                  y={yPos + 3.5}
                  textAnchor="end"
                  className="fill-[var(--text-muted)] text-[10px] sm:text-[11px] font-mono"
                  fontSize="11"
                >
                  {val.toFixed(1)}
                </text>
              </g>
            );
          })}

          {/* Base period reference line (100.0) */}
          {baseLineValue >= minVal && baseLineValue <= maxVal && (
            <g>
              <line
                x1={paddingLeft}
                y1={getY(baseLineValue)}
                x2={chartWidth - paddingRight}
                y2={getY(baseLineValue)}
                stroke="currentColor"
                className="text-[var(--color-gold)] opacity-40"
                strokeWidth="1.2"
                strokeDasharray="4 3"
              />
              <text
                x={chartWidth - paddingRight - 8}
                y={getY(baseLineValue) - 7}
                textAnchor="end"
                className="fill-[var(--color-gold)] text-[10px] sm:text-[11px] font-bold font-mono"
                fontSize="11"
              >
                Base P0 = {baseLineValue.toFixed(1)}
              </text>
            </g>
          )}

          {/* Area Fill Gradient */}
          {data.length > 1 && (
            <polygon
              points={`${getX(0)},${chartHeight - paddingBottom} ${points} ${getX(
                data.length - 1
              )},${chartHeight - paddingBottom}`}
              fill={colorHex}
              fillOpacity="0.12"
            />
          )}

          {/* Main Trend Polyline */}
          {data.length > 1 && (
            <polyline
              fill="none"
              stroke={colorHex}
              strokeWidth="2.8"
              strokeLinecap="round"
              strokeLinejoin="round"
              points={points}
            />
          )}

          {/* Data Points & X-Axis Labels */}
          {data.map((d, i) => {
            const cx = getX(i);
            const cy = getY(d.value);
            const isHovered = hoverIndex === i;

            // If 6 or fewer corridors/points, show ALL labels. Otherwise sample evenly.
            const showLabel =
              data.length <= 7 ||
              i === 0 ||
              i === data.length - 1 ||
              i % Math.ceil(data.length / 6) === 0;

            const displayLabel = allDatesIdentical ? `Pt ${i + 1}` : formatLabel(d.label, i);

            return (
              <g
                key={i}
                onMouseEnter={() => setHoverIndex(i)}
                onMouseLeave={() => setHoverIndex(null)}
                className="cursor-pointer"
              >
                {/* Touch/Mouse Hover Target Area */}
                <circle cx={cx} cy={cy} r="16" fill="transparent" />

                {/* Visible Data Dot */}
                <circle
                  cx={cx}
                  cy={cy}
                  r={isHovered ? 6.5 : 4}
                  fill={colorHex}
                  stroke="var(--bg-card)"
                  strokeWidth="2"
                  className="transition-all duration-150"
                />

                {/* Clean X Axis Label Centered Exactly Under the Dot */}
                {showLabel && (
                  <text
                    x={cx}
                    y={chartHeight - 10}
                    textAnchor="middle"
                    className="fill-[var(--text-secondary)] text-[10px] sm:text-[11px] font-mono font-semibold"
                    fontSize="11"
                  >
                    {displayLabel}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
