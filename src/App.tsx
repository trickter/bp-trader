import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { AdminTokenGate } from "./components/admin-token-gate";
import { DashboardLayout } from "./components/dashboard-layout";
import {
  clearAdminToken,
  getAdminToken,
  setAdminToken,
  subscribeToInvalidAdminToken,
} from "./lib/admin-token";
import { AlertsPage } from "./pages/alerts-page";
import { BacktestsPage } from "./pages/backtests-page";
import { ExecutionPage } from "./pages/execution-page";
import { MarketPulsePage } from "./pages/market-pulse-page";
import { ProfilePage } from "./pages/profile-page";
import { RiskControlsPage } from "./pages/risk-controls-page";
import { SettingsPage } from "./pages/settings-page";
import { StrategiesPage } from "./pages/strategies-page";

export function App() {
  const [adminToken, setAdminTokenState] = useState<string | null>(() => getAdminToken());
  const [authErrorMessage, setAuthErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    return subscribeToInvalidAdminToken(() => {
      setAdminTokenState(null);
      setAuthErrorMessage("The stored admin token was rejected by the backend. Enter a valid token.");
    });
  }, []);

  function handleLogin(token: string) {
    setAdminToken(token);
    setAdminTokenState(token);
    setAuthErrorMessage(null);
  }

  function handleLogout() {
    clearAdminToken();
    setAdminTokenState(null);
    setAuthErrorMessage(null);
  }

  if (!adminToken) {
    return <AdminTokenGate errorMessage={authErrorMessage} onSubmit={handleLogin} />;
  }

  return (
    <Routes>
      <Route path="/" element={<DashboardLayout onLogout={handleLogout} />}>
        <Route index element={<Navigate to="/profile" replace />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="strategies" element={<StrategiesPage />} />
        <Route path="backtests" element={<BacktestsPage />} />
        <Route path="market-pulse" element={<MarketPulsePage />} />
        <Route path="execution" element={<ExecutionPage />} />
        <Route path="risk-controls" element={<RiskControlsPage />} />
        <Route path="alerts" element={<AlertsPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}
