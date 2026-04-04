"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import type { PMCDataPoint } from "@/lib/types";

export function useAerobicPMC(from: string, to: string) {
  const [data, setData] = useState<PMCDataPoint[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchApi<PMCDataPoint[]>(`/api/aerobico/pmc?from_date=${from}&to_date=${to}`)
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
