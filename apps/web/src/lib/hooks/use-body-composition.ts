"use client";

import { useEffect, useRef, useState } from "react";
import { fetchApi } from "@/lib/api";
import type { BodyCompositionDay } from "@/lib/types";

export function useBodyComposition(from: string, to: string) {
  const [data, setData] = useState<BodyCompositionDay[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const prevKeyRef = useRef(`${from}-${to}`);

  useEffect(() => {
    const key = `${from}-${to}`;
    const isNewKey = prevKeyRef.current !== key;
    prevKeyRef.current = key;
    if (isNewKey) {
      setLoading(true);
      setError(null);
    }

    let cancelled = false;
    fetchApi<BodyCompositionDay[]>(`/api/body-composition?from_date=${from}&to_date=${to}`)
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
