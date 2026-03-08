import { useEffect, useState } from "react";

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

  return { data, loading, error };
}
