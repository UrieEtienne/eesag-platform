
import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  OPTIONS_EGLISE_LOCALE,
  OPTION_ADMINISTRATION_EGLISE,
} from "../config/optionsEgliseLocale";

export default function MenuEgliseLocale() {
  const { utilisateur, estAdminLocal, estPasteur } = useAuth();

  // Ce menu ne concerne que les comptes rattachés à une église
  // et autorisés à accéder à l'espace local.
  if (!utilisateur?.eglise || (!estAdminLocal && !estPasteur)) {
    return null;
  }

  const optionsAutorisees = OPTIONS_EGLISE_LOCALE.filter((option) => {
    // Les fonctions réservées à l'administrateur local
    // ne doivent pas être affichées au pasteur.
    if (
      !estAdminLocal &&
      ["annexes", "finances"].includes(option.code)
    ) {
      return false;
    }

    return true;
  });

  return (
    <div className="local-nav-shell">
      <div className="local-nav-title">
        <span>ESPACE DE L'ÉGLISE</span>
        <strong>{utilisateur.eglise_nom || "Mon église"}</strong>
        {utilisateur.eglise_code && (
          <small>{utilisateur.eglise_code}</small>
        )}
      </div>

      <nav
        className="local-nav"
        aria-label="Navigation de l'église locale"
      >
        <div className="local-nav-group">
          <span className="local-nav-group-title">
            {estAdminLocal ? "GESTION DE L'ÉGLISE" : "ESPACE PASTORAL"}
          </span>

          {optionsAutorisees.map((option) => (
            <NavLink
              key={option.code}
              to={option.path}
              end={option.path === "/eglise-dashboard"}
              className={({ isActive }) =>
                `local-nav-item${isActive ? " active" : ""}`
              }
              title={option.description}
            >
              <span className="local-nav-icon" aria-hidden="true">
                {option.icon}
              </span>
              <span className="local-nav-label">{option.label}</span>
            </NavLink>
          ))}
        </div>

        {estAdminLocal && (
          <div className="local-admin-zone">
            <span className="local-nav-group-title">
              ADMINISTRATION
            </span>

            <NavLink
              to={OPTION_ADMINISTRATION_EGLISE.path}
              className={({ isActive }) =>
                `local-nav-item local-nav-admin${isActive ? " active" : ""}`
              }
              title={OPTION_ADMINISTRATION_EGLISE.description}
            >
              <span className="local-nav-icon" aria-hidden="true">
                {OPTION_ADMINISTRATION_EGLISE.icon}
              </span>
              <span className="local-nav-label">
                {OPTION_ADMINISTRATION_EGLISE.label}
              </span>
              <span className="local-admin-badge">ADMIN</span>
            </NavLink>
          </div>
        )}
      </nav>
    </div>
  );
}
