"use client";

import { useEffect, useRef, useState } from "react";
import { fetchApi } from "@/lib/api";
import type { WorkoutWithPlanned } from "@/lib/types";

interface WorkoutSelection {
  id: string;
  type: "completed" | "planned";
}

export function useWorkoutDetail(selection: WorkoutSelection | null) {
  const [data, setData] = useState<WorkoutWithPlanned | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const cacheRef = useRef<Map<string, WorkoutWithPlanned>>(new Map());

  useEffect(() => {
    if (!selection) {
      setData(null);
      setLoading(false);
      return;
    }

    const cacheKey = `${selection.type}:${selection.id}`;
    const cached = cacheRef.current.get(cacheKey);
    if (cached) {
      setData(cached);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    let cancelled = false;
    fetchApi<WorkoutWithPlanned>(
      `/api/aerobico/workout/${selection.id}?type=${selection.type}`,
    )
      .then((result) => {
        if (!cancelled) {
          cacheRef.current.set(cacheKey, result);
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
  }, [selection?.id, selection?.type]);

  return { data, loading, error };
}
