import { useEffect, useState } from "react";
import client from "../api/client";

export default function FormulaireMembre({ egliseId, onFerme, onCree }) {
  const [erreur, setErreur] = useState("");
  const [apercu, setApercu] = useState("");
  const [departements, setDepartements] = useState([]);
  const [rolesEglise, setRolesEglise] = useState([]);
  const [nouveauDepartement, setNouveauDepartement] = useState("");
  const [nouveauRole, setNouveauRole] = useState("");

  const [form, setForm] = useState({
    nom: "",
    prenom: "",
    sexe: "H",
    date_naissance: "",
    telephone: "",
    situation_matrimoniale: "",
    nationalite: "GN",
    date_bapteme_eau: "",
    date_bapteme_saint_esprit: "",
    fonction_eglise: "MEMBRE",
    role: "MEMBRE",
    eglise: egliseId,
    departement: "",
    role_eglise: "",
  });

  const modifier = (champ, valeur) => {
    setForm((f) => ({ ...f, [champ]: valeur }));
  };

  const chargerReferentiels = async () => {
    try {
      const [dep, roles] = await Promise.all([
        client.get("/departements/"),
        client.get("/roles-eglise/", { params: { actif: true } }),
      ]);

      setDepartements(dep.data.results || dep.data || []);
      setRolesEglise(roles.data.results || roles.data || []);
    } catch {
      setErreur("Impossible de charger les départements et rôles.");
    }
  };

  useEffect(() => {
    chargerReferentiels();
  }, []);

  const choisirPhoto = (file) => {
    modifier("photo", file);

    if (!file) {
      setApercu("");
      return;
    }

    const lecteur = new FileReader();
    lecteur.onload = () => setApercu(String(lecteur.result));
    lecteur.readAsDataURL(file);
  };

  const ajouterDepartement = async () => {
    const nom = nouveauDepartement.trim();

    if (!nom) {
      setErreur("Saisissez le nom du département.");
      return;
    }

    setErreur("");

    try {
      const r = await client.post("/departements/", { nom });
      const departement = r.data;

      setDepartements((items) =>
        [...items, departement].sort((a, b) =>
          a.nom.localeCompare(b.nom)
        )
      );

      modifier("departement", String(departement.id));
      setNouveauDepartement("");
    } catch (err) {
      setErreur(
        err.response?.data?.nom?.[0] ||
          err.response?.data?.detail ||
          "Impossible d'ajouter le département."
      );
    }
  };

  const ajouterRole = async () => {
    const nom = nouveauRole.trim();

    if (!nom) {
      setErreur("Saisissez le nom du rôle.");
      return;
    }

    setErreur("");

    try {
      const r = await client.post("/roles-eglise/", {
        nom,
        actif: true,
      });

      const role = r.data;

      setRolesEglise((items) =>
        [...items, role].sort((a, b) => a.nom.localeCompare(b.nom))
      );

      modifier("role_eglise", String(role.id));
      setNouveauRole("");
    } catch (err) {
      setErreur(
        err.response?.data?.nom?.[0] ||
          err.response?.data?.detail ||
          "Impossible d'ajouter le rôle."
      );
    }
  };

  const soumettre = async (e) => {
    e.preventDefault();
    setErreur("");

    try {
      const data = new FormData();

      const payload = {
        ...form,
        eglise: egliseId ?? form.eglise,
        departement: form.departement || "",
        role_eglise: form.role_eglise || "",
      };

      Object.entries(payload).forEach(([cle, valeur]) => {
        if (valeur !== null && valeur !== undefined) {
          data.append(cle, valeur);
        }
      });

      await client.post("/utilisateurs/", data, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      onCree();
    } catch (err) {
      const donnees = err.response?.data || {};

      const premierMessage = (valeur) => {
        if (Array.isArray(valeur)) return valeur[0];
        if (typeof valeur === "string") return valeur;
        return "";
      };

      setErreur(
        premierMessage(donnees.detail) ||
          premierMessage(donnees.telephone) ||
          premierMessage(donnees.situation_matrimoniale) ||
          premierMessage(donnees.departement) ||
          premierMessage(donnees.role_eglise) ||
          premierMessage(donnees.eglise) ||
          "Erreur lors de l'ajout du membre."
      );
    }
  };

  return (
    <div className="modale-fond" onClick={onFerme}>
      <div className="modale" onClick={(e) => e.stopPropagation()}>
        <h3>Ajouter un membre à mon église</h3>

        <p className="sous-titre">
          Le matricule est généré automatiquement. Le membre reste
          rattaché à votre église.
        </p>

        <form onSubmit={soumettre}>
          <div className="form-grid">
            <div className="form-champ">
              <label htmlFor="membre-nom">Nom *</label>
              <input
                id="membre-nom"
                required
                value={form.nom}
                onChange={(e) => modifier("nom", e.target.value)}
              />
            </div>

            <div className="form-champ">
              <label htmlFor="membre-prenom">Prénom *</label>
              <input
                id="membre-prenom"
                required
                value={form.prenom}
                onChange={(e) => modifier("prenom", e.target.value)}
              />
            </div>
          </div>

          <div className="form-grid">
            <div className="form-champ">
              <label htmlFor="membre-sexe">Sexe *</label>
              <select
                id="membre-sexe"
                value={form.sexe}
                onChange={(e) => modifier("sexe", e.target.value)}
                required
              >
                <option value="H">Homme</option>
                <option value="F">Femme</option>
              </select>
            </div>

            <div className="form-champ">
              <label htmlFor="membre-naissance">Date de naissance</label>
              <input
                id="membre-naissance"
                type="date"
                value={form.date_naissance}
                onChange={(e) =>
                  modifier("date_naissance", e.target.value)
                }
              />
            </div>
          </div>

          <div className="form-grid">
            <div className="form-champ">
              <label htmlFor="membre-telephone">Téléphone *</label>
              <input
                id="membre-telephone"
                required
                type="tel"
                value={form.telephone}
                onChange={(e) => modifier("telephone", e.target.value)}
                placeholder="+224..."
                autoComplete="tel"
              />
            </div>

            <div className="form-champ">
              <label htmlFor="membre-matrimonial">
                Situation matrimoniale
              </label>
              <select
                id="membre-matrimonial"
                value={form.situation_matrimoniale}
                onChange={(e) =>
                  modifier("situation_matrimoniale", e.target.value)
                }
              >
                <option value="">Non renseignée</option>
                <option value="CELIBATAIRE">Célibataire</option>
                <option value="FIANCE">Fiancé(e)</option>
                <option value="MARIE">Marié(e)</option>
                <option value="SEPARE">Séparé(e)</option>
                <option value="DIVORCE">Divorcé(e)</option>
                <option value="VEUF">Veuf / Veuve</option>
                <option value="VOEUX_RELIGIEUX">Vœux religieux</option>
                <option value="AUTRE">Autre</option>
              </select>
            </div>
          </div>

          <div className="form-champ">
            <label htmlFor="membre-nationalite">Nationalité</label>
            <select
              id="membre-nationalite"
              value={form.nationalite}
              onChange={(e) => modifier("nationalite", e.target.value)}
            >
              <option value="GN">Guinée</option>
              <option value="SN">Sénégal</option>
              <option value="ML">Mali</option>
              <option value="CI">Côte d’Ivoire</option>
              <option value="LR">Libéria</option>
              <option value="SL">Sierra Leone</option>
              <option value="GH">Ghana</option>
              <option value="NG">Nigéria</option>
              <option value="BF">Burkina Faso</option>
              <option value="FR">France</option>
              <option value="US">États-Unis</option>
              <option value="CA">Canada</option>
              <option value="OTHER">Autre</option>
            </select>
          </div>

          <div className="form-grid">
            <div className="form-champ">
              <label htmlFor="membre-bapteme-eau">Baptême d’eau</label>
              <input
                id="membre-bapteme-eau"
                type="date"
                value={form.date_bapteme_eau}
                onChange={(e) =>
                  modifier("date_bapteme_eau", e.target.value)
                }
              />
            </div>

            <div className="form-champ">
              <label htmlFor="membre-bapteme-esprit">
                Baptême du Saint-Esprit
              </label>
              <input
                id="membre-bapteme-esprit"
                type="date"
                value={form.date_bapteme_saint_esprit}
                onChange={(e) =>
                  modifier("date_bapteme_saint_esprit", e.target.value)
                }
              />
            </div>
          </div>

          <div className="form-grid">
            <div className="form-champ">
              <label htmlFor="membre-departement">Département</label>
              <select
                id="membre-departement"
                value={form.departement}
                onChange={(e) => modifier("departement", e.target.value)}
              >
                <option value="">Aucun</option>
                {departements.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.nom}
                  </option>
                ))}
              </select>

              <div className="inline-create">
                <input
                  aria-label="Nouveau département"
                  value={nouveauDepartement}
                  onChange={(e) => setNouveauDepartement(e.target.value)}
                  placeholder="Nouveau département"
                />
                <button
                  type="button"
                  className="btn btn-secondaire"
                  onClick={ajouterDepartement}
                >
                  ＋ Ajouter
                </button>
              </div>
            </div>

            <div className="form-champ">
              <label htmlFor="membre-role-eglise">Rôle dans l’église</label>
              <select
                id="membre-role-eglise"
                value={form.role_eglise}
                onChange={(e) => modifier("role_eglise", e.target.value)}
              >
                <option value="">Aucun</option>
                {rolesEglise.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.nom}
                  </option>
                ))}
              </select>

              <div className="inline-create">
                <input
                  aria-label="Nouveau rôle dans l’église"
                  value={nouveauRole}
                  onChange={(e) => setNouveauRole(e.target.value)}
                  placeholder="Nouveau rôle"
                />
                <button
                  type="button"
                  className="btn btn-secondaire"
                  onClick={ajouterRole}
                >
                  ＋ Ajouter
                </button>
              </div>
            </div>
          </div>

          <div className="form-champ">
            <label htmlFor="membre-photo">Photo du membre</label>
            <input
              id="membre-photo"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={(e) =>
                choisirPhoto(e.target.files?.[0] || null)
              }
            />

            <small className="sous-titre">
              JPG, PNG ou WebP · maximum 5 Mo.
            </small>

            {apercu && (
              <div className="photo-preview-wrap">
                <img
                  src={apercu}
                  className="photo-preview"
                  alt="Aperçu du membre"
                />
                <span>Aperçu</span>
              </div>
            )}
          </div>

          {erreur && (
            <p className="erreur" role="alert">
              {erreur}
            </p>
          )}

          <div style={{ display: "flex", gap: 10, marginTop: 10 }}>
            <button className="btn" type="submit">
              Enregistrer
            </button>
            <button
              className="btn btn-secondaire"
              type="button"
              onClick={onFerme}
            >
              Annuler
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}