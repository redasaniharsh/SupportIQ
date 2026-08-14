import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import LandingPage from "./pages/LandingPage";
import Dashboard from "./pages/Dashboard";
import IncidentsList from "./pages/IncidentsList";
import IncidentCreate from "./pages/IncidentCreate";
import IncidentDetail from "./pages/IncidentDetail";
import Knowledge from "./pages/Knowledge";
import SearchPage from "./pages/SearchPage";

export default function App() {
  return (
    <Routes>
      {/* Landing page — standalone, no Layout wrapper */}
      <Route path="/" element={<LandingPage />} />

      {/* App routes — wrapped in Layout with header/nav */}
      <Route element={<Layout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/incidents" element={<IncidentsList />} />
        <Route path="/incidents/new" element={<IncidentCreate />} />
        <Route path="/incidents/:id" element={<IncidentDetail />} />
        <Route path="/knowledge" element={<Knowledge />} />
        <Route path="/search" element={<SearchPage />} />
        <Route
          path="*"
          element={
            <div className="state-view state-empty">
              <p>Page not found.</p>
            </div>
          }
        />
      </Route>
    </Routes>
  );
}
