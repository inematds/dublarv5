"use client";

import { useEffect, useState } from "react";

export function NavVersion() {
  const [version, setVersion] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((d) => setVersion(d.version ?? null))
      .catch(() => {});
  }, []);

  if (!version) return null;

  return (
    <span className="text-xs text-gray-500 font-mono ml-1">v{version}</span>
  );
}
