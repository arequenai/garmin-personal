"use client";

import { useEffect, useState } from "react";
import type { UserGoal } from "@/lib/types";
import { fetchApi, mutateApi } from "@/lib/api";

const CATEGORIES = [
  {
    id: "running",
    label: "Running",
    icon: "\u{1F3C3}",
    metrics: [
      { key: "weekly_km", label: "Weekly KM", unit: "km" },
      { key: "vo2max", label: "VO2max", unit: "ml/kg/min" },
      { key: "ctl", label: "CTL", unit: "" },
      { key: "marathon", label: "Marathon Time", unit: "sec" },
    ],
  },
  {
    id: "strength",
    label: "Strength",
    icon: "\u{1F4AA}",
    metrics: [
      { key: "muscle_mass", label: "Muscle Mass", unit: "kg" },
      { key: "strength_days", label: "Training Days", unit: "/wk" },
      { key: "strength_time", label: "Strength Time", unit: "hrs" },
      { key: "pullups", label: "Pull-ups Max", unit: "reps" },
    ],
  },
  {
    id: "recovery",
    label: "Recovery",
    icon: "\u{1F50B}",
    metrics: [
      { key: "recovery_score", label: "Recovery Score", unit: "%" },
      { key: "hrv", label: "HRV", unit: "ms" },
      { key: "body_battery", label: "Body Battery", unit: "%" },
    ],
  },
  {
    id: "sleep",
    label: "Sleep",
    icon: "\u{1F634}",
    metrics: [
      { key: "sleep_score", label: "Sleep Score", unit: "" },
      { key: "sleep_duration", label: "Time in Bed", unit: "min" },
    ],
  },
  {
    id: "body",
    label: "Body Comp + Nutrition",
    icon: "\u2696\uFE0F",
    metrics: [
      { key: "body_fat", label: "Body Fat", unit: "%" },
      { key: "weight", label: "Weight", unit: "kg" },
      { key: "calories", label: "Calories", unit: "kcal" },
      { key: "protein", label: "Protein", unit: "g" },
      { key: "carbs", label: "Carbs", unit: "g" },
      { key: "bmi", label: "BMI", unit: "" },
      { key: "body_water", label: "Body Water", unit: "%" },
      { key: "visceral_fat", label: "Visceral Fat", unit: "" },
    ],
  },
  {
    id: "glucose",
    label: "Glucose",
    icon: "\u{1FA78}",
    metrics: [
      { key: "fasting_glucose", label: "Fasting Glucose", unit: "mg/dL" },
    ],
  },
];

export default function GoalsPage() {
  const [goals, setGoals] = useState<Record<string, number>>({});
  const [saving, setSaving] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    fetchApi<UserGoal[]>("/api/goals")
      .then((data) => {
        const map: Record<string, number> = {};
        for (const g of data) {
          map[g.metric_key] = g.target_value;
        }
        setGoals(map);
        setLoaded(true);
      })
      .catch(() => setLoaded(true));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    const payload: UserGoal[] = [];
    for (const cat of CATEGORIES) {
      for (const m of cat.metrics) {
        if (goals[m.key] !== undefined) {
          payload.push({
            metric_key: m.key,
            target_value: goals[m.key],
            target_unit: m.unit,
            category: cat.id,
          });
        }
      }
    }
    try {
      await mutateApi("/api/goals", "PUT", payload);
    } finally {
      setSaving(false);
    }
  };

  if (!loaded) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-text-secondary">Loading goals...</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl p-8">
      <h1 className="font-heading mb-6 text-2xl font-bold text-text-primary">Goals & Targets</h1>
      <p className="mb-8 text-sm text-text-secondary">
        Set your target values for each metric. These are used in the Overview daily view.
      </p>

      {CATEGORIES.map((cat) => (
        <div key={cat.id} className="mb-8">
          <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-text-primary">
            <span>{cat.icon}</span> {cat.label}
          </h2>
          <div className="space-y-3">
            {cat.metrics.map((m) => (
              <div key={m.key} className="flex items-center gap-4 rounded-xl bg-bg-card px-4 py-3">
                <label className="flex-1 text-sm text-text-secondary">{m.label}</label>
                <input
                  type="number"
                  step="any"
                  value={goals[m.key] ?? ""}
                  onChange={(e) =>
                    setGoals((prev) => ({
                      ...prev,
                      [m.key]: parseFloat(e.target.value) || 0,
                    }))
                  }
                  className="w-24 rounded-lg border border-bg-hover bg-bg-primary px-3 py-1.5 text-right text-sm text-text-primary outline-none focus:border-recovery"
                />
                <span className="w-16 text-xs text-text-secondary">{m.unit}</span>
              </div>
            ))}
          </div>
        </div>
      ))}

      <button
        onClick={handleSave}
        disabled={saving}
        className="rounded-xl bg-recovery px-8 py-3 font-semibold text-black transition-opacity hover:opacity-90 disabled:opacity-50"
      >
        {saving ? "Saving..." : "Save Goals"}
      </button>
    </div>
  );
}
