import { createContext, useContext, useEffect, useState } from "react";
import client from "../api/client";

const AuthContext = createContext(null);

const ROLES_NATIONAUX = ["COORDINATEUR", "SUPERADMIN_INTL", "SUPERADMIN_NATIONAL"];
const ROLES_BUREAU = ["SUPERADMIN_INTL", "SUPERADMIN_NATIONAL"];
const ROLES_GESTION_EGLISE = ["ADMIN_LOCAL", "PASTEUR"];

export function AuthProvider({ children }) {
  const [utilisateur, setUtilisateur] = useState(null);
  const [chargement, setChargement] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setChargement(false);
      return;
    }
    client
      .get("/auth/moi/")
      .then((res) => setUtilisateur(res.data))
      .catch(() => localStorage.clear())
      .finally(() => setChargement(false));
  }, []);

  const connecter = async (identifiant, password) => {
    const { data } = await client.post("/auth/login/", { identifiant, password });
    localStorage.setItem("access_token", data.access);
    localStorage.setItem("refresh_token", data.refresh);
    setUtilisateur(data.utilisateur);
    return data.utilisateur;
  };

  const deconnecter = () => {
    localStorage.clear();
    setUtilisateur(null);
  };

  const estNational = utilisateur && ROLES_NATIONAUX.includes(utilisateur.role);
  const estCoordinateur = utilisateur?.role === "COORDINATEUR" || utilisateur?.is_superuser;
  const estBureauNational = utilisateur && ROLES_BUREAU.includes(utilisateur.role);
  const estGestionnaireEglise = utilisateur && ROLES_GESTION_EGLISE.includes(utilisateur.role);
  const peutGerer = estNational || estGestionnaireEglise;

  return (
    <AuthContext.Provider
      value={{ utilisateur, connecter, deconnecter, chargement, estNational, estCoordinateur, estBureauNational, estGestionnaireEglise, peutGerer }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
