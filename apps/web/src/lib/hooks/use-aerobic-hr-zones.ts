"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import type { HRZonesData } from "@/lib/types";

export function useAerobicHRZones(from: string, to: string) {
  const [data, setData] = useState<HRZonesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [prevKey, setPrevKey] = useState(`${from}-${to}`);

  const key = `${from}-${to}`;
  if (prevKey !== key) {
    setPrevKey(key);
    setLoading(true);
    setError(null);
  }

  useEffect(() => {
    let cancelled = false;

    fetchApi<HRZonesData>(`/api/aerobico/hr-zones?from_date=${from}&to_date=${to}`)
      .then((result) => {
        if (!cancelled) {
          setData(result);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message);
          setLoading(false);
        }
      });

    return () => { cancelled = true; };
  }, [from, to]);

  return { data, loading, error };
}
