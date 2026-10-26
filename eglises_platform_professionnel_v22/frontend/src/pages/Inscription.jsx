import { useState } from "react";
import { useNavigate } from "react-router-dom";
import client from "../api/client";

export default function Inscription() {
  const [form, setForm] = useState({
    identifiant: "",
    telephone: "",
    email: "",
    password: "",
    password_confirmation: "",
  });

  const [otp, setOtp] = useState("");
  const [identifiant, setIdentifiant] = useState("");
  const [testCode, setTestCode] = useState("");
  const [testMode, setTestMode] = useState(false);

  const [etape, setEtape] = useState(1);
  const [erreur, setErreur] = useState("");
  const [chargement, setChargement] = useState(false);

  const nav = useNavigate();

  const modifier = (event) => {
    const { name, value } = event.target;

    setForm((ancien) => ({
      ...ancien,
      [name]: value,
    }));
  };

  const creer = async (event) => {
    event.preventDefault();
    setErreur("");
    setChargement(true);

    try {
      const donnees = {
        identifiant: form.identifiant.trim().toUpperCase(),
        telephone: form.telephone.trim(),
        email: form.email.trim(),
        password: form.password,
        password_confirmation: form.password_confirmation,
      };

      const response = await client.post(
        "/auth/inscription/",
        donnees
      );

      setIdentifiant(response.data.identifiant);

      setTestMode(Boolean(response.data.test_mode));
      setTestCode(response.data.test_code || "");

      setEtape(2);
    } catch (error) {
      const data = error.response?.data;

      const message =
        data?.detail ||
        Object.entries(data || {})
          .map(([champ, messages]) => {
            const texte = Array.isArray(messages)
              ? messages.join(" ")
              : String(messages);

            return `${champ}: ${texte}`;
          })
          .join(" ") ||
        "Impossible de terminer l'inscription.";

      setErreur(message);
    } finally {
      setChargement(false);
    }
  };

  const confirmer = async (event) => {
    event.preventDefault();
    setErreur("");
    setChargement(true);

    try {
      const response = await client.post(
        "/auth/verification-telephone/",
        {
          identifiant,
          code: otp,
        }
      );

      /*
       * Le backend retourne déjà les tokens après
       * confirmation du téléphone.
       *
       * On revient à la connexion pour conserver
       * le fonctionnement actuel de l'application.
       */
      console.log("Compte activé :", response.data);

      nav("/connexion");
    } catch (error) {
      const data = error.response?.data;

      const message =
        data?.detail ||
        Object.values(data || {})
          .flat()
          .join(" ") ||
        "Code de confirmation incorrect ou expiré.";

      setErreur(message);
    } finally {
      setChargement(false);
    }
  };

  return (
    <div className="page-connexion">
      <section className="connexion-brand">
        <div>
          <span className="eyebrow">
            NOUVEAU MEMBRE
          </span>

          <h1>
            Activez votre compte personnel.
          </h1>

          <p>
            Utilisez l'identifiant fourni par votre église,
            confirmez votre téléphone par SMS puis connectez-vous
            à votre espace EESAG.
          </p>
        </div>
      </section>

      <section className="boite-connexion">
        <span className="eyebrow">
          {etape === 1
            ? "INSCRIPTION"
            : "VÉRIFICATION SMS"}
        </span>

        {etape === 1 ? (
          <form onSubmit={creer}>
            <div className="form-champ">
              <label htmlFor="identifiant">
                Identifiant membre
              </label>

              <input
                id="identifiant"
                name="identifiant"
                type="text"
                placeholder="EGL68301-000007"
                value={form.identifiant}
                onChange={(event) =>
                  setForm((ancien) => ({
                    ...ancien,
                    identifiant: event.target.value
                      .toUpperCase()
                      .replace(/[^A-Z0-9-]/g, "")
                      .slice(0, 20),
                  }))
                }
                maxLength={20}
                minLength={14}
                pattern="EGL[0-9]{5}-[0-9]{6}"
                title="Entrez votre identifiant membre, par exemple EGL68301-000007."
                autoComplete="username"
                required
              />

              <small className="helper-text">
                Saisissez l'identifiant qui vous a été fourni
                par votre église.
              </small>
            </div>

            <div className="form-champ">
              <label htmlFor="telephone">
                Téléphone
              </label>

              <input
                id="telephone"
                name="telephone"
                type="tel"
                placeholder="+224626483701"
                value={form.telephone}
                onChange={modifier}
                autoComplete="tel"
                required
              />
            </div>

            <div className="form-champ">
              <label htmlFor="email">
                Email
              </label>

              <input
                id="email"
                name="email"
                type="email"
                placeholder="vous@example.com"
                value={form.email}
                onChange={modifier}
                autoComplete="email"
              />
            </div>

            <div className="form-grid">
              <div className="form-champ">
                <label htmlFor="password">
                  Mot de passe
                </label>

                <input
                  id="password"
                  name="password"
                  type="password"
                  value={form.password}
                  onChange={modifier}
                  autoComplete="new-password"
                  minLength={6}
                  required
                />
              </div>

              <div className="form-champ">
                <label htmlFor="password_confirmation">
                  Confirmation
                </label>

                <input
                  id="password_confirmation"
                  name="password_confirmation"
                  type="password"
                  value={form.password_confirmation}
                  onChange={modifier}
                  autoComplete="new-password"
                  minLength={6}
                  required
                />
              </div>
            </div>

            {erreur && (
              <p className="erreur">
                {erreur}
              </p>
            )}

            <button
              type="submit"
              className="btn"
              disabled={chargement}
            >
              {chargement
                ? "Vérification…"
                : "Créer mon compte"}
            </button>

            <button
              type="button"
              className="btn btn-secondaire"
              onClick={() => nav("/connexion")}
            >
              J'ai déjà un compte
            </button>
          </form>
        ) : (
          <form onSubmit={confirmer}>
            <p className="sous-titre">
              Un code de confirmation a été envoyé
              au numéro indiqué.
            </p>

            <div className="credential-box">
              <small>
                Votre identifiant membre
              </small>

              <strong>
                {identifiant}
              </strong>
            </div>

            {testMode && testCode && (
              <div
                className="credential-box"
                style={{ marginBottom: "16px" }}
              >
                <small>
                  MODE TEST SMS — CODE DE CONFIRMATION
                </small>

                <strong
                  style={{
                    fontSize: "2rem",
                    letterSpacing: "0.3em",
                  }}
                >
                  {testCode}
                </strong>

                <p style={{ margin: 0 }}>
                  Les SMS réels sont désactivés.
                  Utilisez ce code pour terminer
                  l'inscription.
                </p>
              </div>
            )}

            <div className="form-champ">
              <label htmlFor="otp">
                Code SMS à 6 chiffres
              </label>

              <input
                id="otp"
                name="otp"
                inputMode="numeric"
                autoComplete="one-time-code"
                value={otp}
                onChange={(event) =>
                  setOtp(
                    event.target.value
                      .replace(/\D/g, "")
                      .slice(0, 6)
                  )
                }
                maxLength={6}
                minLength={6}
                pattern="[0-9]{6}"
                required
              />
            </div>

            {erreur && (
              <p className="erreur">
                {erreur}
              </p>
            )}

            <button
              type="submit"
              className="btn"
              disabled={chargement}
            >
              {chargement
                ? "Confirmation…"
                : "Confirmer le téléphone"}
            </button>

            <button
              type="button"
              className="btn btn-secondaire"
              onClick={() => setEtape(1)}
            >
              Retour
            </button>
          </form>
        )}
      </section>
    </div>
  );
}