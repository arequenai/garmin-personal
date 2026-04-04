"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import type { CalendarData } from "@/lib/types";

export function useAerobicCalendar(from: string, to: string) {
  const [data, setData] = useState<CalendarData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchApi<CalendarData>(`/api/aerobico/calendar?from_date=${from}&to_date=${to}`)
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
