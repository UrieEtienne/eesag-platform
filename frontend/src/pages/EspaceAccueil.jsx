import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function EspaceAccueil() {
  const { estCoordinateur, estBureauNational, estBureauNationalGeneral, estGestionnaireEglise, estMembre, chargement } = useAuth();
  if (chargement) return <div className="page-loading"><div className="loading-spinner"/><span>Chargement EESAG…</span></div>;
  if (estCoordinateur) return <Navigate to="/national" replace />;
  if (estBureauNationalGeneral) return <Navigate to="/eglises" replace />;
  if (estBureauNational) return <Navigate to="/bureaux" replace />;
  if (estGestionnaireEglise) return <Navigate to="/eglise-dashboard" replace />;
  if (estMembre) return <Navigate to="/bureau-national" replace />;
  return <Navigate to="/connexion" replace />;
}
