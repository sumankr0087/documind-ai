import { useState, useEffect, useCallback } from "react";
import { SystemHealthModel } from "../models";
import { ServiceFactory } from "../services";

export function useSystemHealth() {
  const [health, setHealth] = useState<SystemHealthModel | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = useCallback(async () => {
    try {
      const healthService = ServiceFactory.getInstance().getHealthService();
      const result = await healthService.checkHealth();
      setHealth(result);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to connect to backend");
      setHealth(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    // Poll every 30 seconds
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  return { health, loading, error, refreshHealth: fetchHealth };
}
