"use client";

import { useState } from "react";
import type { PillarData } from "@/lib/types";
import { PillarRow } from "./pillar-row";

interface PillarAccordionProps {
  pillars: PillarData[];
}

export function PillarAccordion({ pillars }: PillarAccordionProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <div className="flex flex-col gap-1">
      {pillars.map((p) => (
        <PillarRow
          key={p.id}
          pillar={p}
          expanded={expandedId === p.id}
          onToggle={() =>
            setExpandedId((prev) => (prev === p.id ? null : p.id))
          }
        />
      ))}
    </div>
  );
}
