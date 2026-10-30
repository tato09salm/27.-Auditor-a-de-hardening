import { QueryClientProvider } from "@tanstack/react-query";
import { ArrowLeft, ShieldOff } from "lucide-react";
import type { ReactNode } from "react";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { Button } from "./components/ui";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ToastProvider } from "./context/Toast";
import { queryClient } from "./lib/queryClient";
import {
  ChangePasswordPage,
  LoadingScreen,
  LoginPage,
  OfflinePage,
  SetupPage,
} from "./pages/AuthPages";
import { DashboardPage } from "./pages/DashboardPage";
import { ServersPage } from "./pages/ServersPage";
import { ServerDetailPage } from "./pages/ServerDetailPage";
import { AuditsPage } from "./pages/AuditsPage";
import { AuditDetailPage } from "./pages/AuditDetailPage";
import { FindingsPage } from "./pages/FindingsPage";
import { FindingDetailPage } from "./pages/FindingDetailPage";
import { RecommendationsPage } from "./pages/RecommendationsPage";
import { RecommendationDetailPage } from "./pages/RecommendationDetailPage";
import { ProfilesPage } from "./pages/ProfilesPage";
import { SchedulesPage } from "./pages/SchedulesPage";
import { ReportsPage } from "./pages/ReportsPage";
import { UsersPage } from "./pages/UsersPage";
import { AuditLogPage } from "./pages/AuditLogPage";
import { SettingsPage } from "./pages/SettingsPage";

function ForbiddenPage() {
  return (
    <div className="mx-auto flex min-h-[50vh] max-w-lg flex-col items-center justify-center text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-red-100 bg-red-50 text-red-600">
        <ShieldOff className="h-6 w-6" />
      </div>
      <h1 className="mt-5 text-xl font-bold text-ink-950">Acceso restringido</h1>
      <p className="mt-2 text-sm leading-6 text-slate-500">
        Su rol no posee el permiso necesario para consultar esta sección. La autorización se verifica
        nuevamente en el backend.
      </p>
      <Link to="/" className="mt-6">
        <Button variant="secondary" icon={<ArrowLeft className="h-4 w-4" />}>
          Volver al dashboard
        </Button>
      </Link>
    </div>
  );
}

function NotFoundPage() {
  return (
    <div className="mx-auto flex min-h-[50vh] max-w-lg flex-col items-center justify-center text-center">
      <p className="text-5xl font-black tracking-tight text-slate-200">404</p>
      <h1 className="mt-3 text-xl font-bold text-ink-950">Página no encontrada</h1>
      <p className="mt-2 text-sm text-slate-500">La ruta solicitada no existe en la consola.</p>
      <Link to="/" className="mt-6">
        <Button>Ir al dashboard</Button>
      </Link>
    </div>
  );
}

function Guard({ permission, children }: { permission: string; children: ReactNode }) {
  const { hasPermission } = useAuth();
  return hasPermission(permission) ? <>{children}</> : <ForbiddenPage />;
}

function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<DashboardPage />} />
        <Route
          path="servers"
          element={
            <Guard permission="servers:read">
              <ServersPage />
            </Guard>
          }
        />
        <Route
          path="servers/:serverId"
          element={
            <Guard permission="servers:read">
              <ServerDetailPage />
            </Guard>
          }
        />
        <Route
          path="audits"
          element={
            <Guard permission="audits:read">
              <AuditsPage />
            </Guard>
          }
        />
        <Route
          path="audits/:runId"
          element={
            <Guard permission="audits:read">
              <AuditDetailPage />
            </Guard>
          }
        />
        <Route
          path="findings"
          element={
            <Guard permission="findings:read">
              <FindingsPage />
            </Guard>
          }
        />
        <Route
          path="findings/:findingId"
          element={
            <Guard permission="findings:read">
              <FindingDetailPage />
            </Guard>
          }
        />
        <Route
          path="recommendations"
          element={
            <Guard permission="recommendations:read">
              <RecommendationsPage />
            </Guard>
          }
        />
        <Route
          path="recommendations/:recommendationId"
          element={
            <Guard permission="recommendations:read">
              <RecommendationDetailPage />
            </Guard>
          }
        />
        <Route
          path="profiles"
          element={
            <Guard permission="profiles:read">
              <ProfilesPage />
            </Guard>
          }
        />
        <Route
          path="schedules"
          element={
            <Guard permission="schedules:manage">
              <SchedulesPage />
            </Guard>
          }
        />
        <Route
          path="reports"
          element={
            <Guard permission="reports:read">
              <ReportsPage />
            </Guard>
          }
        />
        <Route
          path="users"
          element={
            <Guard permission="users:read">
              <UsersPage />
            </Guard>
          }
        />
        <Route
          path="audit-log"
          element={
            <Guard permission="logs:read">
              <AuditLogPage />
            </Guard>
          }
        />
        <Route
          path="settings"
          element={
            <Guard permission="settings:manage">
              <SettingsPage />
            </Guard>
          }
        />
        <Route path="change-password" element={<ChangePasswordPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

function Root() {
  const { stage, user } = useAuth();
  if (stage === "loading") return <LoadingScreen />;
  if (stage === "offline") return <OfflinePage />;
  if (stage === "setup") return <SetupPage />;
  if (stage === "login" || !user) return <LoginPage />;
  if (user.must_change_password) return <ChangePasswordPage forced />;
  return <AppRoutes />;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <AuthProvider>
          <BrowserRouter>
            <Root />
          </BrowserRouter>
        </AuthProvider>
      </ToastProvider>
    </QueryClientProvider>
  );
}
