import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function RouteProtegee({
  children,
  roles = [],
  finance = false,
}) {
  const {
    utilisateur,
    chargement,
    peutGererFinances,
  } = useAuth();

  if (chargement) {
    return (
      <div className="page-chargement">
        Chargement EESAG…
      </div>
    );
  }

  if (!utilisateur) {
    return <Navigate to="/connexion" replace />;
  }

  if (roles.length && !roles.includes(utilisateur.role)) {
    return <Navigate to="/" replace />;
  }

  if (finance && !peutGererFinances) {
    return <Navigate to="/" replace />;
  }

  return children;
}