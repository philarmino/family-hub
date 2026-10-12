import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import KidsPage from "./pages/KidsPage";
import ParentsPage from "./pages/ParentsPage";

export default function App() {
  const location = useLocation();
  const isParents = location.pathname.startsWith("/eltern");

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to="/" className="brand">
          Family Hub
        </Link>
        <nav className="nav">
          <Link to="/" className={!isParents ? "nav-link active" : "nav-link"}>
            Kinder
          </Link>
          <Link
            to="/eltern"
            className={isParents ? "nav-link active" : "nav-link"}
          >
            Eltern
          </Link>
        </nav>
      </header>
      <main className="main">
        <Routes>
          <Route path="/" element={<KidsPage />} />
          <Route path="/eltern/*" element={<ParentsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
