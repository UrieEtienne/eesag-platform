import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Connexion() {
  const [identifiant, setIdentifiant] = useState("");
  const [password, setPassword] = useState("");
  const [afficherPassword, setAfficherPassword] = useState(false);
  const [erreur, setErreur] = useState("");
  const [enCours, setEnCours] = useState(false);

  const { connecter } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const soumettre = async (e) => {
    e.preventDefault();
    setErreur("");

    const id = identifiant.trim();

    if (!id || !password) {
      setErreur("Veuillez saisir votre identifiant et votre mot de passe.");
      return;
    }

    setEnCours(true);

    try {
      const user = await connecter(id, password);

      if (!user) {
        setErreur("La connexion n'a pas abouti. Vérifiez vos identifiants.");
        return;
      }

      const destination = location.state?.from?.pathname;

      if (destination && destination !== "/connexion") {
        navigate(destination, { replace: true });
        return;
      }

      if (
        user.role === "COORDINATEUR" ||
        user.role === "SUPERADMIN_INTL" ||
        user.role === "SUPERADMIN_NATIONAL"
      ) {
        navigate("/national", { replace: true });
      } else {
        navigate("/", { replace: true });
      }
    } catch (err) {
      setErreur(
        err.response?.data?.detail ||
          "Connexion impossible. Vérifiez votre identifiant et votre mot de passe. Si votre compte vient d'être créé, confirmez d'abord votre numéro de téléphone."
      );
    } finally {
      setEnCours(false);
    }
  };

  return (
    <div className="page-connexion">
      <section className="connexion-brand">
        <div>
          <span className="eyebrow">PORTAIL SÉCURISÉ EESAG</span>

          <h1>
            Un réseau d'églises.
            <br />
            Un espace pour chacune.
          </h1>

          <p>
            Connectez-vous à votre espace personnel pour accéder aux
            fonctionnalités autorisées selon votre rôle au sein de l'EESAG.
          </p>
        </div>
      </section>

      <section className="boite-connexion">
        <span className="eyebrow">CONNEXION</span>

        <h1>Accéder à mon espace</h1>

        <p className="sous-titre">
          Saisissez votre identifiant personnel et votre mot de passe.
        </p>

        {location.state?.message && (
          <p className="status-active">{location.state.message}</p>
        )}

        <form onSubmit={soumettre}>
          <div className="form-champ">
            <label htmlFor="identifiant">Identifiant personnel</label>

            <input
              id="identifiant"
              name="identifiant"
              type="text"
              autoComplete="username"
              autoCapitalize="characters"
              spellCheck={false}
              value={identifiant}
              onChange={(e) => setIdentifiant(e.target.value)}
              placeholder="EGL93065-000003"
              disabled={enCours}
              required
            />

            <small>
              Utilisez l'identifiant qui vous a été attribué par votre église.
            </small>
          </div>

          <div className="form-champ">
            <label htmlFor="password">Mot de passe</label>

            <div className="champ-password">
              <input
                id="password"
                name="password"
                type={afficherPassword ? "text" : "password"}
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={enCours}
                required
              />

              <button
                type="button"
                className="password-toggle"
                onClick={() => setAfficherPassword((visible) => !visible)}
                disabled={enCours}
                aria-label={
                  afficherPassword
                    ? "Masquer le mot de passe"
                    : "Afficher le mot de passe"
                }
                aria-pressed={afficherPassword}
                title={
                  afficherPassword
                    ? "Masquer le mot de passe"
                    : "Afficher le mot de passe"
                }
              >
                {afficherPassword ? (
                  /* Œil barré : masquer */
                  <svg
                    viewBox="0 0 24 24"
                    width="22"
                    height="22"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <path d="M3 3l18 18" />
                    <path d="M10.6 10.6a2 2 0 002.8 2.8" />
                    <path d="M9.9 5.2A11.5 11.5 0 0112 5c5 0 8.5 4.5 9.5 7-.4 1-1.2 2.2-2.4 3.4" />
                    <path d="M6.2 6.2C3.9 7.7 2.6 10 2 12c1 2.5 4.5 7 10 7 1.3 0 2.5-.3 3.5-.8" />
                  </svg>
                ) : (
                  /* Œil ouvert : afficher */
                  <svg
                    viewBox="0 0 24 24"
                    width="22"
                    height="22"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          {erreur && (
            <p className="erreur" role="alert">
              {erreur}
            </p>
          )}

          <button className="btn" type="submit" disabled={enCours}>
            {enCours ? "Connexion en cours…" : "Se connecter"}
          </button>

          <button
            type="button"
            className="btn btn-secondaire"
            disabled={enCours}
            onClick={() => navigate("/inscription")}
          >
            Créer mon compte membre
          </button>
        </form>
      </section>
    </div>
  );
}