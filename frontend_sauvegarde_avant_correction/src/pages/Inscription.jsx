
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import client from "../api/client";

const FORM_INITIAL = {
  identifiant: "",
  telephone: "",
  email: "",
  password: "",
  password_confirmation: "",
};

function messageErreur(err, messageParDefaut) {
  const data = err?.response?.data;

  if (typeof data?.detail === "string") {
    return data.detail;
  }

  if (data && typeof data === "object") {
    return Object.entries(data)
      .map(([champ, valeur]) => {
        const texte = Array.isArray(valeur)
          ? valeur.join(" ")
          : String(valeur);

        return champ === "non_field_errors" || champ === "detail"
          ? texte
          : `${champ} : ${texte}`;
      })
      .join(" ");
  }

  return messageParDefaut;
}

export default function Inscription() {
  const navigate = useNavigate();

  const [formulaire, setFormulaire] = useState(FORM_INITIAL);
  const [etape, setEtape] = useState(1);
  const [identifiant, setIdentifiant] = useState("");
  const [otp, setOtp] = useState("");
  const [testCode, setTestCode] = useState("");
  const [testMode, setTestMode] = useState(false);
  const [erreur, setErreur] = useState("");
  const [message, setMessage] = useState("");
  const [enCours, setEnCours] = useState(false);

  function modifierChamp(e) {
    const { name, value } = e.target;

    setFormulaire((precedent) => ({
      ...precedent,
      [name]:
        name === "identifiant"
          ? value.trimStart().toUpperCase()
          : value,
    }));

    setErreur("");
    setMessage("");
  }

  async function creerCompte(e) {
    e.preventDefault();
    setErreur("");
    setMessage("");

    const id = formulaire.identifiant.trim().toUpperCase();

    if (!id) {
      setErreur("Veuillez saisir votre identifiant de membre.");
      return;
    }

    if (
      !formulaire.telephone.trim() ||
      !formulaire.password ||
      !formulaire.password_confirmation
    ) {
      setErreur("Veuillez remplir tous les champs obligatoires.");
      return;
    }

    if (formulaire.password.length < 6) {
      setErreur("Le mot de passe doit contenir au moins 6 caractères.");
      return;
    }

    if (formulaire.password !== formulaire.password_confirmation) {
      setErreur("Les deux mots de passe ne correspondent pas.");
      return;
    }

    setEnCours(true);

    try {
      const reponse = await client.post("/auth/inscription/", {
        identifiant: id,
        telephone: formulaire.telephone.trim(),
        email: formulaire.email.trim(),
        password: formulaire.password,
        password_confirmation: formulaire.password_confirmation,
      });

      setIdentifiant(reponse.data.identifiant || id);
      setTestMode(Boolean(reponse.data.test_mode));
      setTestCode(reponse.data.test_code || "");
      setOtp("");
      setEtape(2);

      setMessage(
        reponse.data.detail ||
          "Vérifiez votre numéro de téléphone pour terminer l'inscription."
      );
    } catch (err) {
      setErreur(
        messageErreur(err, "Impossible de démarrer l'inscription.")
      );
    } finally {
      setEnCours(false);
    }
  }

  async function confirmerTelephone(e) {
    e.preventDefault();
    setErreur("");
    setMessage("");

    if (!/^\d{6}$/.test(otp)) {
      setErreur("Saisissez le code de confirmation à 6 chiffres.");
      return;
    }

    setEnCours(true);

    try {
      await client.post("/auth/verification-telephone/", {
        identifiant,
        code: otp,
      });

      setMessage(
        "Votre numéro est confirmé. Vous pouvez maintenant vous connecter."
      );

      navigate("/connexion", {
        replace: true,
        state: {
          message:
            "Inscription confirmée. Connectez-vous avec votre identifiant et votre mot de passe.",
          identifiant,
        },
      });
    } catch (err) {
      setErreur(
        messageErreur(err, "Impossible de confirmer le numéro de téléphone.")
      );
    } finally {
      setEnCours(false);
    }
  }

  async function renvoyerCode() {
    setErreur("");
    setMessage("");
    setEnCours(true);

    try {
      const reponse = await client.post(
        "/auth/renvoyer-code-telephone/",
        { identifiant }
      );

      setTestMode(Boolean(reponse.data.test_mode));
      setTestCode(reponse.data.test_code || "");
      setMessage(
        reponse.data.detail || "Demande de nouveau code traitée."
      );
    } catch (err) {
      setErreur(
        messageErreur(err, "Impossible de renvoyer le code.")
      );
    } finally {
      setEnCours(false);
    }
  }

  return (
    <div className="page-connexion">
      <section className="connexion-brand">
        <div>
          <span className="eyebrow">NOUVEAU MEMBRE</span>
          <h1>Créer mon compte personnel.</h1>
          <p>
            Utilisez l'identifiant attribué par votre église,
            puis confirmez votre numéro pour terminer l'inscription.
          </p>
        </div>
      </section>

      <section className="boite-connexion">
        <span className="eyebrow">
          {etape === 1 ? "INSCRIPTION DU MEMBRE" : "VÉRIFICATION DU NUMÉRO"}
        </span>

        {etape === 1 ? (
          <form onSubmit={creerCompte}>
            <div className="form-champ">
              <label htmlFor="identifiant">
                Identifiant du membre *
              </label>
              <input
                id="identifiant"
                name="identifiant"
                value={formulaire.identifiant}
                onChange={modifierChamp}
                placeholder="EGL93065-000003"
                autoComplete="username"
                maxLength={20}
                required
              />
              <small>
                Saisissez l'identifiant qui vous a été fourni par votre église.
              </small>
            </div>

            <div className="form-champ">
              <label htmlFor="telephone">
                Téléphone enregistré auprès de l'église *
              </label>
              <input
                id="telephone"
                name="telephone"
                type="tel"
                value={formulaire.telephone}
                onChange={modifierChamp}
                placeholder="+224622000000"
                autoComplete="tel"
                maxLength={20}
                required
              />
            </div>

            <div className="form-champ">
              <label htmlFor="email">E-mail (facultatif)</label>
              <input
                id="email"
                name="email"
                type="email"
                value={formulaire.email}
                onChange={modifierChamp}
                placeholder="vous@exemple.com"
                autoComplete="email"
              />
            </div>

            <div className="form-champ">
              <label htmlFor="password">Mot de passe *</label>
              <input
                id="password"
                name="password"
                type="password"
                value={formulaire.password}
                onChange={modifierChamp}
                autoComplete="new-password"
                minLength={6}
                required
              />
            </div>

            <div className="form-champ">
              <label htmlFor="password_confirmation">
                Confirmer le mot de passe *
              </label>
              <input
                id="password_confirmation"
                name="password_confirmation"
                type="password"
                value={formulaire.password_confirmation}
                onChange={modifierChamp}
                autoComplete="new-password"
                minLength={6}
                required
              />
            </div>

            {erreur && <p className="erreur" role="alert">{erreur}</p>}

            <button className="btn" type="submit" disabled={enCours}>
              {enCours ? "Vérification…" : "Créer mon compte"}
            </button>

            <button
              className="btn btn-secondaire"
              type="button"
              onClick={() => navigate("/connexion")}
              disabled={enCours}
            >
              J'ai déjà un compte
            </button>
          </form>
        ) : (
          <form onSubmit={confirmerTelephone}>
            <p className="sous-titre">
              Identifiant : <strong>{identifiant}</strong>
            </p>

            {message && (
              <p role="status" aria-live="polite">{message}</p>
            )}

            {testMode && testCode && (
              <div
                className="credential-box"
                style={{ marginBottom: 16 }}
              >
                <small>MODE TEST SMS — CODE DE CONFIRMATION</small>
                <strong
                  style={{
                    display: "block",
                    fontSize: "2rem",
                    letterSpacing: "0.3em",
                  }}
                >
                  {testCode}
                </strong>
                <p>
                  Les SMS réels sont désactivés. Utilisez ce code pour tester
                  la confirmation.
                </p>
              </div>
            )}

            <div className="form-champ">
              <label htmlFor="otp">Code de confirmation à 6 chiffres *</label>
              <input
                id="otp"
                name="otp"
                inputMode="numeric"
                autoComplete="one-time-code"
                value={otp}
                onChange={(e) =>
                  setOtp(e.target.value.replace(/\D/g, "").slice(0, 6))
                }
                maxLength={6}
                pattern="[0-9]{6}"
                placeholder="123456"
                required
              />
            </div>

            {erreur && <p className="erreur" role="alert">{erreur}</p>}

            <button className="btn" type="submit" disabled={enCours}>
              {enCours ? "Confirmation…" : "Confirmer mon numéro"}
            </button>

            <button
              className="btn btn-secondaire"
              type="button"
              onClick={renvoyerCode}
              disabled={enCours}
            >
              Renvoyer le code
            </button>

            <button
              className="btn btn-secondaire"
              type="button"
              onClick={() => {
                setEtape(1);
                setErreur("");
                setMessage("");
              }}
              disabled={enCours}
            >
              Retour au formulaire
            </button>
          </form>
        )}
      </section>
    </div>
  );
}
