import { Navigate, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import client from "../api/client";

function FonctionnaliteVerrouillee() {
  return (
    <div className="feature-locked-page">
      <div className="feature-locked-icon">🔒</div>
      <span className="eyebrow">ACCÈS VERROUILLÉ</span>
      <h1>Fonctionnalité indisponible</h1>
      <p>
        Cette fonctionnalité a été désactivée par le propriétaire du système.
        Aucun autre utilisateur ne peut la réactiver.
      </p>
    </div>
  );
}

export default function RouteProtegee({ children, roles, feature }) {
  const { utilisateur, chargement } = useAuth();
  const location = useLocation();
  const [allowed, setAllowed] = useState(feature ? null : true);

  useEffect(() => {
    if (!feature || !utilisateur) {
      setAllowed(true);
      return;
    }

    let live = true;
    client.get("/systeme/fonctionnalites/")
      .then((r) => {
        if (!live) return;
        const f = (Array.isArray(r.data) ? r.data : []).find((x) => x.code === feature);
        setAllowed(f ? f.actif !== false : true);
      })
      .catch(() => {
        if (live) setAllowed(false);
      });

    return () => { live = false; };
  }, [feature, utilisateur?.id]);

  if (chargement || allowed === null) {
    return (
      <div className="page-loading">
        <div className="loading-spinner" />
        <span>Chargement EESAG…</span>
      </div>
    );
  }

  if (!utilisateur) {
    return <Navigate to="/connexion" replace state={{ from: location.pathname }} />;
  }

  if (roles?.length && !roles.includes(utilisateur.role)) {
    return <Navigate to="/" replace />;
  }

  if (feature && !allowed) {
    return <FonctionnaliteVerrouillee />;
  }

  return children;
}
