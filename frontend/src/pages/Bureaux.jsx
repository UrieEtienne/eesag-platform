import { useCallback, useEffect, useMemo, useState } from "react";
import client, { mediaUrl } from "../api/client";
import { useAuth } from "../context/AuthContext";
import GestionComptesBureau from "./GestionComptesBureau";

const ANNEE = new Date().getFullYear();

function liste(data) {
const value = data?.results ?? data;
return Array.isArray(value) ? value : [];
}

const TYPES = {
FEMMES: "♀",
JEUNESSE: "★",
ENFANTS: "◉",
EVANGELISATION: "✦",
HOMMES: "♂",
FAMILLES: "❤",
COMMUNICATION: "◌",
MUSIQUE: "♪",
MISSIONS: "✦",
};

const TYPES_NATIONAUX = [
{ value: "HOMMES", label: "Bureau national des Hommes" },
{ value: "FEMMES", label: "Bureau national des Femmes" },
{ value: "JEUNESSE", label: "Bureau national de la Jeunesse" },
{ value: "ENFANTS", label: "Bureau national des Enfants" },
];

function messageErreurApi(error, defaut) {
const data = error?.response?.data;

if (typeof data === "string") return data;
if (data?.detail) return data.detail;

if (data && typeof data === "object") {
return Object.values(data)
.flat()
.filter(Boolean)
.join(" ");
}

return defaut;
}

export default function Bureaux() {
const {
estNational,
estCoordinateur,
utilisateur,
estGestionnaireEglise,
} = useAuth();

const [bureaux, setBureaux] = useState([]);
const [selection, setSelection] = useState(null);
const [membres, setMembres] = useState([]);
const [annee, setAnnee] = useState(ANNEE);

const [erreur, setErreur] = useState("");
const [message, setMessage] = useState("");
const [chargement, setChargement] = useState(true);
const [chargementMembres, setChargementMembres] = useState(false);

const [ajout, setAjout] = useState(false);
const [creationBureauOuverte, setCreationBureauOuverte] = useState(false);
const [creationBureauEnCours, setCreationBureauEnCours] = useState(false);

const [formBureau, setFormBureau] = useState({
nom: "",
type_bureau: "HOMMES",
description: "",
});

const [form, setForm] = useState({
nom_complet: "",
poste: "",
photo: null,
annee: ANNEE,
});

const peutVoirLocaux = Boolean(estGestionnaireEglise);
const peutAdministrer = Boolean(
selection?.mes_droits?.peut_gerer_membres
);

const chargerBureaux = useCallback(async () => {
setChargement(true);
setErreur("");

try {
  const params =
    estNational || !peutVoirLocaux
      ? { niveau: "NATIONAL", actif: true }
      : {
          niveau: "LOCAL",
          eglise: utilisateur?.eglise,
          actif: true,
        };

  const res = await client.get("/bureaux/", { params });
  const data = liste(res.data);

  setBureaux(data);

  setSelection((ancienneSelection) => {
    if (!data.length) return null;

    if (ancienneSelection) {
      return (
        data.find((b) => b.id === ancienneSelection.id) || data[0]
      );
    }

    return data[0];
  });
} catch (error) {
  setErreur(
    messageErreurApi(error, "Impossible de charger les bureaux.")
  );
} finally {
  setChargement(false);
}

}, [estNational, peutVoirLocaux, utilisateur?.eglise]);

const chargerMembres = useCallback(async () => {
if (!selection?.id) {
setMembres([]);
return;
}

setChargementMembres(true);

try {
  const res = await client.get("/bureau-membres-independants/", {
    params: {
      bureau: selection.id,
      annee,
      actif: true,
    },
  });

  setMembres(liste(res.data));
} catch (error) {
  setMembres([]);
  setErreur(
    messageErreurApi(
      error,
      "Impossible de charger les membres de ce bureau."
    )
  );
} finally {
  setChargementMembres(false);
}

}, [selection?.id, annee]);

useEffect(() => {
if (utilisateur) {
chargerBureaux();
}
}, [utilisateur, chargerBureaux]);

useEffect(() => {
chargerMembres();
}, [chargerMembres]);

const creerBureauNational = async (e) => {
e.preventDefault();
setErreur("");
setMessage("");

if (!estCoordinateur) {
  setErreur(
    "Seul le Coordinateur du système peut créer un bureau national."
  );
  return;
}

if (!formBureau.nom.trim()) {
  setErreur("Le nom du bureau est obligatoire.");
  return;
}

setCreationBureauEnCours(true);

try {
  const res = await client.post("/bureaux/", {
    nom: formBureau.nom.trim(),
    niveau: "NATIONAL",
    type_bureau: formBureau.type_bureau,
    description: formBureau.description.trim(),
    actif: true,
  });

  const nouveauBureau = res.data;

  setCreationBureauOuverte(false);
  setFormBureau({
    nom: "",
    type_bureau: "HOMMES",
    description: "",
  });

  setMessage(
   "Le bureau national " +
    nouveauBureau.nom +
    " a été créé avec succès."
  );

  await chargerBureaux();

  if (nouveauBureau.id) {
    setSelection(nouveauBureau);
  }
} catch (error) {
  setErreur(
    messageErreurApi(
      error,
      "La création du bureau national a échoué."
    )
  );
} finally {
  setCreationBureauEnCours(false);
}

};

const ajouterMembre = async (e) => {
e.preventDefault();
setErreur("");
setMessage("");

if (!selection) {
  setErreur("Sélectionne d'abord un bureau.");
  return;
}

if (!form.nom_complet.trim() || !form.poste.trim()) {
  setErreur("Le nom complet et le poste sont obligatoires.");
  return;
}

try {
  const data = new FormData();

  data.append("bureau", String(selection.id));
  data.append("nom_complet", form.nom_complet.trim());
  data.append("poste", form.poste.trim());
  data.append("annee", String(annee));
  data.append("actif", "true");

  if (form.photo) {
    data.append("photo", form.photo);
  }

  await client.post("/bureau-membres-independants/", data);

  setForm({
    nom_complet: "",
    poste: "",
    photo: null,
    annee,
  });

  setAjout(false);
  setMessage(
    "Le membre du bureau a été ajouté sans créer de compte utilisateur."
  );

  await chargerMembres();
} catch (error) {
  setErreur(
    messageErreurApi(error, "L'ajout du membre a été refusé.")
  );
}

};

const compteur = useMemo(
() =>
bureaux.reduce(
(total, bureau) =>
total + Number(bureau.membres_actifs || 0),
0
),
[bureaux]
);

const typesNationauxDisponibles = TYPES_NATIONAUX.filter(
(type) =>
!bureaux.some(
(bureau) =>
bureau.niveau === "NATIONAL" &&
bureau.type_bureau === type.value
)
);

return ( <div className="bureaux-page"> <div className="page-hero bureau-hero"> <div> <span className="eyebrow">GOUVERNANCE EESAG</span>

      <h1>
        {estNational || !peutVoirLocaux
          ? "Bureaux nationaux"
          : "Bureaux internes de l’église"}
      </h1>

      <p>
        Consulte les structures et leur composition, avec les photos
        et les postes des membres.
      </p>
    </div>

    <div className="hero-side-stat">
      <strong>{bureaux.length}</strong>
      <span>structures accessibles</span>
      <small>{compteur} membre(s) actif(s)</small>
    </div>
  </div>

  {erreur && (
    <div className="console-error" role="alert">
      {erreur}
    </div>
  )}

  {message && (
    <div className="console-success" role="status">
      {message}
    </div>
  )}

  {estCoordinateur && (
    <section className="carte mb-4">
      <div className="section-header">
        <div>
          <span className="eyebrow">ADMINISTRATION CENTRALE</span>
          <h3>Créer un bureau national</h3>
          <p>
            Le Bureau national des Hommes doit être créé en premier.
          </p>
        </div>

        <button
          type="button"
          className="btn"
          onClick={() => {
            setCreationBureauOuverte((ouverte) => !ouverte);
            setErreur("");
            setMessage("");
          }}
        >
          {creationBureauOuverte
            ? "Fermer"
            : "+ Créer un bureau national"}
        </button>
      </div>

      {creationBureauOuverte && (
        <form
          className="bureau-add-form bureau-add-form-large"
          onSubmit={creerBureauNational}
        >
          <div className="form-champ">
            <label htmlFor="type-bureau-national">
              Type de bureau national
            </label>

            <select
              id="type-bureau-national"
              required
              value={formBureau.type_bureau}
              onChange={(e) => {
                const type = e.target.value;
                const libelle = TYPES_NATIONAUX.find(
                  (item) => item.value === type
                )?.label;

                setFormBureau((ancien) => ({
                  ...ancien,
                  type_bureau: type,
                  nom: ancien.nom || libelle || "",
                }));
              }}
            >
              {typesNationauxDisponibles.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}

              {bureaux.some(
                (bureau) =>
                  bureau.type_bureau === formBureau.type_bureau
              ) && (
                <option value={formBureau.type_bureau}>
                  {TYPES_NATIONAUX.find(
                    (item) =>
                      item.value === formBureau.type_bureau
                  )?.label || formBureau.type_bureau}
                </option>
              )}
            </select>

            {typesNationauxDisponibles.length === 0 && (
              <small>
                Tous les types de bureaux nationaux proposés existent déjà.
              </small>
            )}
          </div>

          <div className="form-champ">
            <label htmlFor="nom-bureau-national">
              Nom du bureau
            </label>

            <input
              id="nom-bureau-national"
              required
              maxLength={150}
              value={formBureau.nom}
              onChange={(e) =>
                setFormBureau((ancien) => ({
                  ...ancien,
                  nom: e.target.value,
                }))
              }
              placeholder="Ex. Bureau national des Hommes EESAG"
            />
          </div>

          <div className="form-champ">
            <label htmlFor="description-bureau-national">
              Description (facultative)
            </label>

            <textarea
              id="description-bureau-national"
              rows={3}
              value={formBureau.description}
              onChange={(e) =>
                setFormBureau((ancien) => ({
                  ...ancien,
                  description: e.target.value,
                }))
              }
              placeholder="Responsabilités et missions du bureau"
            />
          </div>

          <button
            className="btn"
            type="submit"
            disabled={
              creationBureauEnCours ||
              typesNationauxDisponibles.length === 0
            }
          >
            {creationBureauEnCours
              ? "Création en cours..."
              : "Enregistrer le bureau national"}
          </button>
        </form>
      )}
    </section>
  )}

  <div className="bureaux-layout">
    <section className="carte bureaux-list-card">
      <div className="section-header">
        <div>
          <span className="eyebrow">BUREAUX</span>
          <h3>Choisir un bureau</h3>
        </div>
      </div>

      {chargement ? (
        <div className="empty-state">Chargement…</div>
      ) : (
        <div className="bureau-select-list">
          {bureaux.map((bureau) => (
            <button
              type="button"
              key={bureau.id}
              className={`bureau-select-row ${
                selection?.id === bureau.id ? "selected" : ""
              }`}
              onClick={() => setSelection(bureau)}
            >
              <span className="bureau-select-icon">
                {TYPES[bureau.type_bureau] || "◆"}
              </span>

              <span>
                <b>{bureau.nom}</b>
                <small>{bureau.code}</small>
              </span>

              <strong>{bureau.membres_actifs || 0}</strong>
            </button>
          ))}

          {!bureaux.length && (
            <div className="empty-state">
              Aucun bureau accessible.
            </div>
          )}
        </div>
      )}
    </section>

    <section className="carte bureau-members-card bureau-members-showcase">
      {!selection ? (
        <div className="empty-state large-empty">
          <span>◆</span>
          <h3>Choisissez un bureau</h3>
          <p>
            Les membres apparaîtront ici avec leur photo, leur nom
            complet et leur poste.
          </p>
        </div>
      ) : (
        <>
          <div className="section-header bureau-detail-header">
            <div>
              <span className="eyebrow">{selection.code}</span>
              <h3>{selection.nom}</h3>
              <p>
                {selection.description || "Composition du bureau."}
              </p>
            </div>

            <select
              value={annee}
              onChange={(e) => setAnnee(Number(e.target.value))}
              aria-label="Année"
            >
              <option value={ANNEE}>{ANNEE}</option>
              <option value={ANNEE - 1}>{ANNEE - 1}</option>
              <option value={ANNEE + 1}>{ANNEE + 1}</option>
            </select>
          </div>

          {peutAdministrer && (
            <div className="bureau-admin-toolbar">
              <button
                type="button"
                className="btn"
                onClick={() => setAjout((value) => !value)}
              >
                {ajout
                  ? "Fermer"
                  : "+ Ajouter un membre du bureau"}
              </button>

              <small>
                Cette fiche est indépendante des comptes utilisateurs.
              </small>
            </div>
          )}

          {ajout && peutAdministrer && (
            <form
              className="bureau-add-form bureau-add-form-large"
              onSubmit={ajouterMembre}
            >
              <div className="form-champ">
                <label htmlFor="membre-nom">Nom complet</label>
                <input
                  id="membre-nom"
                  required
                  value={form.nom_complet}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      nom_complet: e.target.value,
                    })
                  }
                  placeholder="Ex. Marie K. Diallo"
                />
              </div>

              <div className="form-champ">
                <label htmlFor="membre-poste">
                  Poste pour {annee}
                </label>
                <input
                  id="membre-poste"
                  required
                  value={form.poste}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      poste: e.target.value,
                    })
                  }
                  placeholder="Présidente, Secrétaire, Trésorière…"
                />
              </div>

              <div className="form-champ">
                <label htmlFor="membre-photo">Photo</label>
                <input
                  id="membre-photo"
                  type="file"
                  accept="image/*"
                  onChange={(e) =>
                    setForm({
                      ...form,
                      photo: e.target.files?.[0] || null,
                    })
                  }
                />
              </div>

              <button className="btn" type="submit">
                Enregistrer la composition
              </button>
            </form>
          )}

          <div className="bureau-members-grid bureau-members-grid-large">
            {chargementMembres ? (
              <div className="empty-state">
                Chargement des membres…
              </div>
            ) : (
              <>
                {membres.map((membre) => (
                  <article
                    className="bureau-member-card bureau-member-card-large"
                    key={membre.id}
                  >
                    <div className="bureau-member-photo bureau-member-photo-large">
                      {membre.photo_url || membre.photo ? (
                        <img
                          src={mediaUrl(
                            membre.photo_url || membre.photo
                          )}
                          alt={membre.nom_complet}
                        />
                      ) : (
                        <img
                          src="/assets/logo_eesag.jpg"
                          alt="EESAG"
                        />
                      )}
                    </div>

                    <div className="bureau-member-info-large">
                      <h4>{membre.nom_complet}</h4>
                      <p>{membre.poste}</p>
                      <small>Mandat {membre.annee}</small>
                    </div>
                  </article>
                ))}

                {!membres.length && (
                  <div className="empty-state">
                    Aucun membre enregistré pour {annee}.
                  </div>
                )}
              </>
            )}
          </div>
        </>
      )}
    </section>
  </div>
</div>

);
}

