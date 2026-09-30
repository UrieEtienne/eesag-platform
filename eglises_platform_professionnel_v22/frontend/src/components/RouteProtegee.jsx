import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function RouteProtegee({
  children,
  roles = [],
}) {
  const {
    utilisateur,
    chargement,
  } = useAuth();

  const location = useLocation();

  /*
  |--------------------------------------------------------------------------
  | CHARGEMENT
  |--------------------------------------------------------------------------
  */

  if (chargement) {
    return (
      <div className="page-loading">
        Chargement de votre espace...
      </div>
    );
  }

  /*
  |--------------------------------------------------------------------------
  | NON CONNECTE
  |--------------------------------------------------------------------------
  */

  if (!utilisateur) {
    return (
      <Navigate
        to="/connexion"
        replace
        state={{
          from: location.pathname,
        }}
      />
    );
  }

  /*
  |--------------------------------------------------------------------------
  | VERIFICATION ROLE
  |--------------------------------------------------------------------------
  */

  if (roles.length > 0) {
    const roleUtilisateur =
      utilisateur?.role?.toUpperCase?.() || "";

    const autorise = roles
      .map((role) => role.toUpperCase())
      .includes(roleUtilisateur);

    /*
     * Le superuser Django est assimilé au Coordinateur.
     */

    const estSuperuser =
      utilisateur?.is_superuser === true;

    if (!autorise && !(
      estSuperuser &&
      roles.includes("COORDINATEUR")
    )) {
      return (
        <Navigate
          to="/"
          replace
        />
      );
    }
  }

  return children;
}