
import { useEffect, useState } from "react";
import client from "../api/client";

const DROITS = [
  ["peut_gerer_membres", "Gérer les membres du bureau"],
  ["peut_gerer_finances", "Gérer les finances"],
  ["peut_gerer_projets", "Gérer les projets"],
  ["peut_envoyer_notifications", "Envoyer des notifications"],
  ["peut_gerer_rapports", "Gérer les rapports"],
  ["peut_gerer_utilisateurs", "Créer et gérer les autres administrateurs"],
];

const formulaireInitial = {
  nom: "",
  prenom: "",
  sexe: "H",
  telephone: "",
  email: "",
  poste: "",
  annee: new Date().getFullYear(),
  objectif_annuel: "",
};

const droitsInitiaux = {
  peut_gerer_membres: true,
  peut_gerer_finances: false,
  peut_gerer_projets: false,
  peut_envoyer_notifications: false,
  peut_gerer_rapports: false,
  peut_gerer_utilisateurs: false,
};

export default function GestionComptesBureau() {
  const [bureaux, setBureaux] = useState([]);
  const [bureauId, setBureauId] = useState("");
  const [typeCompte, setTypeCompte] = useState("membre");
  const [form, setForm] = useState(formulaireInitial);
  const [droits, setDroits] = useState(droitsInitiaux);
  const [chargement, setChargement] = useState(true);
  const [envoi, setEnvoi] = useState(false);
  const [erreur, setErreur] = useState("");
  const [message, setMessage] = useState("");
  const [identifiant, setIdentifiant] = useState("");

  useEffect(() => {
    let actif = true;

    client.get("/bureaux/")
      .then((response) => {
        const donnees = response.data?.results ?? response.data ?? [];
        const nationaux = donnees.filter(
          (bureau) =>
            bureau.niveau === "NATIONAL" && bureau.actif
        );

        if (actif) {
          setBureaux(nationaux);
          if (nationaux.length) {
            setBureauId(String(nationaux[0].id));
          }
        }
      })
      .catch(() => {
        if (actif) {
          setErreur("Impossible de charger les bureaux nationaux.");
        }
      })
      .finally(() => {
        if (actif) setChargement(false);
      });

    return () => {
      actif = false;
    };
  }, []);

  const bureauSelectionne = bureaux.find(
    (bureau) => String(bureau.id) === String(bureauId)
  );

  const mesDroits = bureauSelectionne?.mes_droits ?? {};
  const peutCreerMembre =
    mesDroits.peut_gerer_membres === true;
  const peutCreerAdmin =
    mesDroits.peut_gerer_utilisateurs === true;

  const modifier = (event) => {
    const { name, value } = event.target;
    setForm((ancien) => ({ ...ancien, [name]: value }));
  };

  const soumettre = async (event) => {
    event.preventDefault();
    setErreur("");
    setMessage("");
    setIdentifiant("");

    if (!bureauId) {
      setErreur("Sélectionnez un bureau national.");
      return;
    }

    if (typeCompte === "membre" && !peutCreerMembre) {
      setErreur("Vous n'avez pas le droit de créer des membres.");
      return;
    }

    if (typeCompte === "admin" && !peutCreerAdmin) {
      setErreur("Vous n'avez pas le droit de créer des administrateurs.");
      return;
    }

    if (!form.nom.trim() || !form.prenom.trim() ||
        !form.telephone.trim() || !form.poste.trim()) {
      setErreur("Nom, prénom, téléphone et poste sont obligatoires.");
      return;
    }

    const donnees = {
      nom: form.nom.trim(),
      prenom: form.prenom.trim(),
      sexe: form.sexe,
      telephone: form.telephone.trim(),
      email: form.email.trim(),
      poste: form.poste.trim(),
      annee: Number(form.annee),
      objectif_annuel: form.objectif_annuel,
    };

    if (typeCompte === "admin") {
      Object.assign(donnees, droits);
    }

    setEnvoi(true);

    try {
      const action =
        typeCompte === "membre"
          ? "creer-membre"
          : "creer-administrateur";

      const response = await client.post(
        `/bureaux/${bureauId}/${action}/`,
        donnees
      );

      setIdentifiant(response.data?.identifiant ?? "");
      setMessage(
        response.data?.detail ??
        "Le compte a été créé. Vérifiez le statut de confirmation."
      );
      setForm(formulaireInitial);
    } catch (error) {
      const data = error.response?.data;
      const detail =
        data?.detail ||
        Object.entries(data || {})
          .map(([champ, valeur]) =>
            `${champ}: ${
              Array.isArray(valeur) ? valeur.join(", ") : valeur
            }`
          )
          .join(" — ");

      setErreur(detail || "La création du compte a échoué.");
    } finally {
      setEnvoi(false);
    }
  };

  if (chargement) return <p>Chargement des bureaux nationaux…</p>;

  return (
    <section className="gestion-comptes-bureau">
      <header>
        <h1>Gestion des comptes du Bureau national</h1>
        <p>
          Créez les membres et les administrateurs en respectant
          les permissions attribuées à votre compte.
        </p>
      </header>

      {erreur && (
        <div className="alert alert-danger" role="alert">
          {erreur}
        </div>
      )}

      {message && (
        <div className="alert alert-success" role="status">
          <p>{message}</p>
          {identifiant && (
            <p>
              <strong>Identifiant de connexion :</strong>{" "}
              <code>{identifiant}</code>
            </p>
          )}
          <p>
            Le compte doit confirmer son téléphone avant de pouvoir
            se connecter si la confirmation OTP est requise.
          </p>
        </div>
      )}

      <form onSubmit={soumettre}>
        <label htmlFor="bureauId">Bureau national</label>
        <select
          id="bureauId"
          value={bureauId}
          onChange={(event) => setBureauId(event.target.value)}
          required
        >
          {bureaux.map((bureau) => (
            <option key={bureau.id} value={bureau.id}>
              {bureau.nom} ({bureau.code})
            </option>
          ))}
        </select>

        {!bureaux.length && (
          <p>Aucun bureau national actif n'est disponible.</p>
        )}

        {bureauSelectionne && (
          <p>
            Permissions disponibles :{" "}
            {peutCreerMembre ? "membres" : ""}
            {peutCreerMembre && peutCreerAdmin ? " · " : ""}
            {peutCreerAdmin ? "administrateurs" : ""}
            {!peutCreerMembre && !peutCreerAdmin
              ? "aucune permission de création"
              : ""}
          </p>
        )}

        <fieldset>
          <legend>Type de compte à créer</legend>

          <label>
            <input
              type="radio"
              name="typeCompte"
              value="membre"
              checked={typeCompte === "membre"}
              onChange={() => setTypeCompte("membre")}
            />
            Membre du bureau
          </label>

          <label>
            <input
              type="radio"
              name="typeCompte"
              value="admin"
              checked={typeCompte === "admin"}
              onChange={() => setTypeCompte("admin")}
            />
            Administrateur du bureau
          </label>
        </fieldset>

        <div className="form-grid">
          <label>
            Nom
            <input name="nom" value={form.nom}
              onChange={modifier} required />
          </label>

          <label>
            Prénom
            <input name="prenom" value={form.prenom}
              onChange={modifier} required />
          </label>

          <label>
            Sexe
            <select name="sexe" value={form.sexe} onChange={modifier}>
              <option value="H">Homme</option>
              <option value="F">Femme</option>
            </select>
          </label>

          <label>
            Téléphone
            <input name="telephone" type="tel"
              value={form.telephone} onChange={modifier} required />
          </label>

          <label>
            Email
            <input name="email" type="email"
              value={form.email} onChange={modifier} />
          </label>

          <label>
            Poste dans le bureau
            <input name="poste" value={form.poste}
              onChange={modifier} required />
          </label>

          <label>
            Année du mandat
            <input name="annee" type="number"
              min="2000" max="2100" value={form.annee}
              onChange={modifier} required />
          </label>
        </div>

        <label>
          Objectif annuel
          <textarea
            name="objectif_annuel"
            value={form.objectif_annuel}
            onChange={modifier}
            rows={3}
          />
        </label>

        {typeCompte === "admin" && (
          <fieldset>
            <legend>Permissions de cet administrateur</legend>
            {DROITS.map(([cle, libelle]) => (
              <label key={cle} className="permission-item">
                <input
                  type="checkbox"
                  checked={Boolean(droits[cle])}
                  onChange={(event) =>
                    setDroits((ancien) => ({
                      ...ancien,
                      [cle]: event.target.checked,
                    }))
                  }
                  disabled={
                    mesDroits[cle] !== true &&
                    !peutCreerAdmin
                  }
                />
                {libelle}
              </label>
            ))}
          </fieldset>
        )}

        <button
          type="submit"
          disabled={
            envoi ||
            !bureauId ||
            (typeCompte === "membre" && !peutCreerMembre) ||
            (typeCompte === "admin" && !peutCreerAdmin)
          }
        >
          {envoi
            ? "Création en cours…"
            : typeCompte === "membre"
              ? "Créer le membre"
              : "Créer l'administrateur"}
        </button>
      </form>
    </section>
  );
}