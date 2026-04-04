"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import type { HRZonesData } from "@/lib/types";

export function useAerobicHRZones(from: string, to: string) {
  const [data, setData] = useState<HRZonesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const toDate = new Date(to);
    const fourWeeksBack = new Date(toDate);
    fourWeeksBack.setDate(fourWeeksBack.getDate() - 28);
    const effectiveFrom = fourWeeksBack.toISOString().split("T")[0];

    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchApi<HRZonesData>(`/api/aerobico/hr-zones?from_date=${effectiveFrom}&to_date=${to}`)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [from, to]);

  return { data, loading, error };
}
