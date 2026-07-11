import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { Dashboard } from "@/pages/Dashboard";
import { InvestigationsList } from "@/pages/InvestigationsList";
import { Investigation } from "@/pages/Investigation";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Dashboard />} />
        <Route path="investigations" element={<InvestigationsList />} />
        <Route path="investigations/:customerId" element={<Investigation />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
