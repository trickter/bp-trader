import { Navigate, Route, Routes } from "react-router-dom";

import { DashboardLayout } from "./components/dashboard-layout";
import { AlertsPage } from "./pages/alerts-page";
import { BacktestsPage } from "./pages/backtests-page";
import { ExecutionPage } from "./pages/execution-page";
import { MarketPulsePage } from "./pages/market-pulse-page";
import { ProfilePage } from "./pages/profile-page";
import { RiskControlsPage } from "./pages/risk-controls-page";
import { SettingsPage } from "./pages/settings-page";
import { StrategiesPage } from "./pages/strategies-page";

export function App() {
  return (
    <Routes>
      <Route path="/" element={<DashboardLayout />}>
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
