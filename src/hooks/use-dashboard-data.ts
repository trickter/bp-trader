import { useEffect, useState } from "react";

type DashboardStatus = "loading" | "error" | "empty" | "success";

export function useDashboardData<T>(load: () => Promise<T>, initialData: T) {
  const [data, setData] = useState<T>(initialData);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    void load()
      .then((result) => {
        if (!active) {
          return;
        }

        setData(result);
        setError(null);
      })
      .catch((cause: unknown) => {
        if (!active) {
          return;
        }

        setData(initialData);
        setError(cause instanceof Error ? cause.message : "Unknown error");
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [load]);

  const isEmptyArray = Array.isArray(data) && data.length === 0;
  const isEmptyObject =
    !Array.isArray(data) &&
    typeof data === "object" &&
    data !== null &&
    Object.keys(data).length === 0;
  const status: DashboardStatus = loading
    ? "loading"
    : error
      ? "error"
      : isEmptyArray || isEmptyObject
        ? "empty"
        : "success";

  return { data, loading, error, status };
}
