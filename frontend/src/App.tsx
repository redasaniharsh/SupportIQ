import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import IncidentsList from "./pages/IncidentsList";
import IncidentCreate from "./pages/IncidentCreate";
import IncidentDetail from "./pages/IncidentDetail";
import Knowledge from "./pages/Knowledge";
import SearchPage from "./pages/SearchPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/incidents" element={<IncidentsList />} />
        <Route path="/incidents/new" element={<IncidentCreate />} />
        <Route path="/incidents/:id" element={<IncidentDetail />} />
        <Route path="/knowledge" element={<Knowledge />} />
        <Route path="/search" element={<SearchPage />} />
        <Route
          path="*"
          element={
            <div className="state-view state-empty">
              <div className="state-icon" aria-hidden="true">
                📭
              </div>
              <p>Page not found.</p>
            </div>
          }
        />
      </Route>
    </Routes>
  );
}
