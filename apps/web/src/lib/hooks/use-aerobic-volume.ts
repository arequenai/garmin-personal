"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import type { WeeklyVolume } from "@/lib/types";

export function useAerobicVolume(from: string, to: string) {
  const [data, setData] = useState<WeeklyVolume[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchApi<WeeklyVolume[]>(`/api/aerobico/volume?from_date=${from}&to_date=${to}`)
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
