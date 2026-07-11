import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { Dashboard } from "@/pages/Dashboard";
import { InvestigationsList } from "@/pages/InvestigationsList";
import { Investigation } from "@/pages/Investigation";
import { Customers } from "@/pages/Customers";
import { Alerts } from "@/pages/Alerts";
import { Cases } from "@/pages/Cases";
import { CaseDetail } from "@/pages/CaseDetail";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Dashboard />} />
        <Route path="investigations" element={<InvestigationsList />} />
        <Route path="investigations/:customerId" element={<Investigation />} />
        <Route path="customers" element={<Customers />} />
        <Route path="alerts" element={<Alerts />} />
        <Route path="cases/open" element={<Cases kind="open" />} />
        <Route path="cases/closed" element={<Cases kind="closed" />} />
        <Route path="cases/detail/:caseId" element={<CaseDetail />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
