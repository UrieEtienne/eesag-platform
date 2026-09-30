import { createContext, useContext, useEffect, useState } from "react";
import client from "../api/client";

const AuthContext = createContext(null);

/*
|--------------------------------------------------------------------------
| ROLES
|--------------------------------------------------------------------------
*/

const ROLES_NATIONAUX = [
  "COORDINATEUR",
  "SUPERADMIN_INTL",
  "SUPERADMIN_NATIONAL",
];

const ROLES_BUREAU = [
  "SUPERADMIN_INTL",
  "SUPERADMIN_NATIONAL",
];

const ROLES_GESTION_EGLISE = [
  "ADMIN_LOCAL",
  "PASTEUR",
];

export function AuthProvider({ children }) {
  const [utilisateur, setUtilisateur] = useState(null);
  const [bureaux, setBureaux] = useState([]);
  const [chargement, setChargement] = useState(true);

  /*
  |--------------------------------------------------------------------------
  | RECUPERATION UTILISATEUR CONNECTE
  |--------------------------------------------------------------------------
  */

  useEffect(() => {
    const token = localStorage.getItem("access_token");

    if (!token) {
      setChargement(false);
      return;
    }

    client
      .get("/auth/moi/")
      .then((res) => {
        setUtilisateur(res.data);
      })
      .catch(() => {
        localStorage.clear();
        setUtilisateur(null);
        setBureaux([]);
      })
      .finally(() => {
        setChargement(false);
      });
  }, []);

  /*
  |--------------------------------------------------------------------------
  | CONNEXION
  |--------------------------------------------------------------------------
  */

  const connecter = async (identifiant, password) => {
    const { data } = await client.post("/auth/login/", {
      identifiant,
      password,
    });

    localStorage.setItem("access_token", data.access);
    localStorage.setItem("refresh_token", data.refresh);

    setUtilisateur(data.utilisateur);

    return data.utilisateur;
  };

  /*
  |--------------------------------------------------------------------------
  | DECONNEXION
  |--------------------------------------------------------------------------
  */

  const deconnecter = () => {
    localStorage.clear();
    setUtilisateur(null);
    setBureaux([]);
  };

  /*
  |--------------------------------------------------------------------------
  | ROLES
  |--------------------------------------------------------------------------
  */

  const role = utilisateur?.role?.toUpperCase?.() || "";

  const estCoordinateur = Boolean(
    role === "COORDINATEUR" ||
    utilisateur?.is_superuser === true
  );

  const estNational = Boolean(
    ROLES_NATIONAUX.includes(role)
  );

  const estBureauNational = Boolean(
    ROLES_BUREAU.includes(role)
  );

  const estAdminLocal = Boolean(
    role === "ADMIN_LOCAL"
  );

  const estPasteur = Boolean(
    role === "PASTEUR"
  );

  const estResponsableDepartement = Boolean(
    role === "RESPONSABLE_DEPARTEMENT"
  );

  const estMembre = Boolean(
    role === "MEMBRE"
  );

  const estGestionnaireEglise = Boolean(
    ROLES_GESTION_EGLISE.includes(role)
  );

  /*
  |--------------------------------------------------------------------------
  | BUREAU NATIONAL
  |--------------------------------------------------------------------------
  |
  | On ne bloque plus l'accès sur bureaux.length.
  | Le rôle SUPERADMIN_INTL / SUPERADMIN_NATIONAL suffit.
  |
  */

  const estBureauNationalGeneral = estBureauNational;

  /*
  |--------------------------------------------------------------------------
  | PERMISSIONS COORDINATEUR
  |--------------------------------------------------------------------------
  */

  const peutAdministrerSysteme = estCoordinateur;

  const peutGererUtilisateursGlobaux = estCoordinateur;

  const peutControlerBureauNational = estCoordinateur;

  const peutControlerToutesLesEglises = estCoordinateur;

  const peutGererFonctionnalites = estCoordinateur;

  const peutPublierAnnonces = estCoordinateur;

  /*
  |--------------------------------------------------------------------------
  | PERMISSIONS BUREAU NATIONAL
  |--------------------------------------------------------------------------
  */

  const peutGererEglises = Boolean(
    estCoordinateur ||
    estBureauNational
  );

  const peutCreerEglise = Boolean(
    estCoordinateur ||
    estBureauNational
  );

  const peutActiverDesactiverEglise = Boolean(
    estCoordinateur ||
    estBureauNational
  );

  const peutCreerAdminEglise = Boolean(
    estCoordinateur ||
    estBureauNational
  );

  /*
  |--------------------------------------------------------------------------
  | PERMISSIONS EGLISE LOCALE
  |--------------------------------------------------------------------------
  */

  const peutAdministrerEglise = Boolean(
    estCoordinateur ||
    estAdminLocal
  );

  const peutGererEglise = Boolean(
    estCoordinateur ||
    estAdminLocal ||
    estPasteur
  );

  const peutGererMembres = Boolean(
    estCoordinateur ||
    estAdminLocal ||
    estPasteur
  );

  const peutGererUtilisateursEglise = Boolean(
    estCoordinateur ||
    estAdminLocal
  );

  /*
  |--------------------------------------------------------------------------
  | COURRIERS
  |--------------------------------------------------------------------------
  */

  const peutEnvoyerCourriers = Boolean(
    estCoordinateur ||
    estAdminLocal ||
    estPasteur
  );

  const peutRecevoirCourriers = Boolean(
    estCoordinateur ||
    estAdminLocal ||
    estPasteur
  );

  /*
  |--------------------------------------------------------------------------
  | COMPATIBILITE ANCIEN CODE
  |--------------------------------------------------------------------------
  */

  const peutGerer = Boolean(
    estNational ||
    estGestionnaireEglise
  );

  /*
  |--------------------------------------------------------------------------
  | CONTEXTE
  |--------------------------------------------------------------------------
  */

  return (
    <AuthContext.Provider
      value={{
        utilisateur,
        bureaux,

        setUtilisateur,
        setBureaux,

        connecter,
        deconnecter,
        chargement,

        // rôles
        role,
        estNational,
        estCoordinateur,
        estBureauNational,
        estBureauNationalGeneral,
        estGestionnaireEglise,
        estAdminLocal,
        estPasteur,
        estResponsableDepartement,
        estMembre,

        // permissions système
        peutAdministrerSysteme,
        peutGererUtilisateursGlobaux,
        peutControlerBureauNational,
        peutControlerToutesLesEglises,
        peutGererFonctionnalites,
        peutPublierAnnonces,

        // permissions Bureau national
        peutGererEglises,
        peutCreerEglise,
        peutActiverDesactiverEglise,
        peutCreerAdminEglise,

        // permissions église
        peutAdministrerEglise,
        peutGererEglise,
        peutGererMembres,
        peutGererUtilisateursEglise,

        // courriers
        peutEnvoyerCourriers,
        peutRecevoirCourriers,

        // compatibilité
        peutGerer,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);