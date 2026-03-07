"use client";

import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis } from "recharts";

interface TrendChartProps {
  data: Array<Record<string, unknown>>;
  dataKey: string;
  xAxisKey?: string;
  color?: string;
  height?: number;
  showXAxis?: boolean;
  showTooltip?: boolean;
  gradientFill?: boolean;
}

export function TrendChart({
  data,
  dataKey,
  xAxisKey = "date",
  color = "#22c55e",
  height = 200,
  showXAxis = true,
  showTooltip = true,
  gradientFill = true,
}: TrendChartProps) {
  const gradientId = `gradient-${dataKey}`;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
        <defs>
          {gradientFill && (
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.25} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          )}
        </defs>

        {showXAxis && (
          <XAxis
            dataKey={xAxisKey}
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#6b6b7b", fontSize: 12 }}
            dy={8}
          />
        )}

        {showTooltip && (
          <Tooltip
            contentStyle={{
              backgroundColor: "#12121a",
              border: "none",
              borderRadius: "0.75rem",
              boxShadow: "0 4px 24px rgba(0,0,0,0.4)",
              color: "#e8e8ed",
              fontSize: "0.875rem",
            }}
            itemStyle={{ color: "#e8e8ed" }}
            labelStyle={{ color: "#6b6b7b", marginBottom: 4 }}
            cursor={{ stroke: color, strokeWidth: 1, strokeDasharray: "4 4" }}
          />
        )}

        <Area
          type="monotone"
          dataKey={dataKey}
          stroke={color}
          strokeWidth={2}
          fill={gradientFill ? `url(#${gradientId})` : "transparent"}
          dot={false}
          activeDot={{
            r: 4,
            fill: color,
            stroke: "#12121a",
            strokeWidth: 2,
          }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
