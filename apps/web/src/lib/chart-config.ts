import { ColorType } from "lightweight-charts";

/** Shared base options for all lightweight-charts instances. */
export const BASE_CHART_OPTIONS = {
  layout: {
    background: { type: ColorType.Solid, color: "#1a1a1a" },
    textColor: "#888888",
  },
  grid: {
    vertLines: { color: "#2a2a2a" },
    horzLines: { color: "#2a2a2a" },
  },
  crosshair: { mode: 0 as const },
  handleScroll: { mouseWheel: false },
  handleScale: { mouseWheel: false },
  rightPriceScale: { borderColor: "#2a2a2a" },
  timeScale: { borderColor: "#2a2a2a" },
} as const;
