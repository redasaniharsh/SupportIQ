import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useState, type FormEvent } from "react";
import { Search } from "lucide-react";

export default function Layout() {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  function onSearchSubmit(e: FormEvent) {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header-inner">
          <NavLink to="/" className="brand" end>
            <span aria-hidden="true">🤖</span> AI Service Desk
          </NavLink>
          <nav className="main-nav" aria-label="Main navigation">
            <NavLink to="/" end className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}>
              Dashboard
            </NavLink>
            <NavLink to="/incidents" className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}>
              🎫 Incidents
            </NavLink>
            <NavLink to="/knowledge" className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}>
              📚 Knowledge
            </NavLink>
          </nav>
          <form className="global-search" role="search" onSubmit={onSearchSubmit}>
            <label htmlFor="global-search-input" className="sr-only">
              Search incidents and knowledge base
            </label>
            <Search size={16} aria-hidden="true" />
            <input
              id="global-search-input"
              type="search"
              placeholder="Search everything..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </form>
          <NavLink to="/incidents/new" className="btn btn-primary">
            + New Incident
          </NavLink>
        </div>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
