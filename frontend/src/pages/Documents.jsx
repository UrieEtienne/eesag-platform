
import { useCallback, useEffect, useMemo, useState } from "react";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";

const extraireListe = (data) => {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  if (Array.isArray(data?.data)) return data.data;
  return [];
};

export default function Documents() {
  const { estNational, utilisateur, peutGerer } = useAuth();

  const [documents, setDocuments] = useState([]);
  const [eglises, setEglises] = useState([]);
  const [recherche, setRecherche] = useState("");
  const [afficher, setAfficher] = useState(false);
  const [erreur, setErreur] = useState("");
  const [chargement, setChargement] = useState(true);
  const [chargementEglises, setChargementEglises] = useState(false);

  const charger = useCallback(async () => {
    setChargement(true);
    setErreur("");

    try {
      const response = await client.get("/documents/");
      setDocuments(extraireListe(response.data));
    } catch (err) {
      setDocuments([]);
      setErreur(
        err.response?.data?.detail ||
          "Impossible de charger les documents."
      );
    } finally {
      setChargement(false);
    }
  }, []);

  const chargerEglises = useCallback(async () => {
    if (!peutGerer) return;

    setChargementEglises(true);

    try {
      const response = await client.get("/eglises/");
      setEglises(extraireListe(response.data));
    } catch (err) {
      setErreur(
        err.response?.data?.detail ||
          "Impossible de charger la liste des églises."
      );
    } finally {
      setChargementEglises(false);
    }
  }, [peutGerer]);

  useEffect(() => {
    charger();
  }, [charger]);

  useEffect(() => {
    chargerEglises();
  }, [chargerEglises]);

  const marquer = async (id) => {
    setErreur("");

    try {
      await client.post(`/documents/${id}/marquer_recu/`);
      await charger();
    } catch (err) {
      setErreur(
        err.response?.data?.detail ||
          "Impossible de confirmer la réception."
      );
    }
  };

  const filtrerEglises = useMemo(() => {
    const terme = recherche.trim().toLowerCase();

    return eglises.filter((eglise) => {
      if (!terme) return true;

      return `${eglise.nom || ""} ${eglise.code || ""}`
        .toLowerCase()
        .includes(terme);
    });
  }, [eglises, recherche]);

  const totalDocuments = documents.length;

  const documentsRecus = documents.filter((document) => {
    const reception = document.destinataires_resume?.find(
      (item) => String(item.eglise) === String(utilisateur?.eglise)
    );

    return Boolean(reception?.compte_reception);
  }).length;

  const documentsNonLus = documents.filter((document) => {
    const reception = document.destinataires_resume?.find(
      (item) => String(item.eglise) === String(utilisateur?.eglise)
    );

    return reception && !reception.lu;
  }).length;

  const ouvrirFormulaire = () => {
    setErreur("");
    setRecherche("");
    setAfficher(true);
  };

  return (
    <div className="page-shell page-documents">
      {/* EN-TÊTE */}
      <section className="page-hero documents-hero">
        <div className="documents-hero-content">
          <span className="eyebrow">ESPACE DOCUMENTAIRE EESAG</span>

          <h1>Gestion des documents</h1>

          <p>
            Consultez, partagez et suivez les documents officiels
            échangés entre le Bureau national et les églises.
          </p>

          <div className="documents-hero-info">
            <span>
              <span className="documents-indicator" />
              Espace documentaire sécurisé
            </span>

            <span>
              {utilisateur?.eglise_nom ||
                (estNational ? "Coordination nationale" : "Mon espace")}
            </span>
          </div>
        </div>

        {peutGerer && (
          <button
            type="button"
            className="btn documents-create-btn"
            onClick={ouvrirFormulaire}
          >
            <span>＋</span> Envoyer un document
          </button>
        )}
      </section>

      {/* ERREUR */}
      {erreur && (
        <div className="console-error" role="alert">
          {erreur}
        </div>
      )}

      {/* INDICATEURS */}
      <section className="documents-stats">
        <article className="documents-stat-card">
          <div className="documents-stat-icon documents-icon-blue">
            <span>▤</span>
          </div>

          <div>
            <span className="documents-stat-label">
              Documents accessibles
            </span>
            <strong>{chargement ? "…" : totalDocuments}</strong>
          </div>
        </article>

        <article className="documents-stat-card">
          <div className="documents-stat-icon documents-icon-green">
            <span>✓</span>
          </div>

          <div>
            <span className="documents-stat-label">
              Réceptions confirmées
            </span>
            <strong>{chargement ? "…" : documentsRecus}</strong>
          </div>
        </article>

        <article className="documents-stat-card">
          <div className="documents-stat-icon documents-icon-gold">
            <span>◷</span>
          </div>

          <div>
            <span className="documents-stat-label">
              Documents non lus
            </span>
            <strong>{chargement ? "…" : documentsNonLus}</strong>
          </div>
        </article>
      </section>

      {/* LISTE DES DOCUMENTS */}
      <section className="carte documents-list-card">
        <div className="documents-list-header">
          <div>
            <span className="eyebrow">ARCHIVES ET PARTAGES</span>
            <h3>Documents disponibles</h3>
            <p>
              Retrouvez les documents transmis dans votre périmètre.
            </p>
          </div>

          <span className="documents-count">
            {totalDocuments} document{totalDocuments > 1 ? "s" : ""}
          </span>
        </div>

        <div className="documents-table-container">
          {chargement ? (
            <div className="empty-state">
              Chargement des documents…
            </div>
          ) : documents.length === 0 ? (
            <div className="documents-empty">
              <div className="documents-empty-icon">▤</div>
              <h3>Aucun document disponible</h3>
              <p>
                Les documents qui vous seront transmis apparaîtront ici.
              </p>
            </div>
          ) : (
            <div className="table-wrap">
              <table className="documents-table">
                <thead>
                  <tr>
                    <th>Document</th>
                    <th>Catégorie</th>
                    <th>Expéditeur</th>
                    <th>Destinataire</th>
                    <th>Réception</th>
                    <th>Actions</th>
                  </tr>
                </thead>

                <tbody>
                  {documents.map((document) => {
                    const reception =
                      document.destinataires_resume?.find(
                        (item) =>
                          String(item.eglise) ===
                          String(utilisateur?.eglise)
                      );

                    const statut = reception
                      ? reception.compte_reception
                        ? "confirmé"
                        : reception.lu
                          ? "lu"
                          : "non-lu"
                      : "indisponible";

                    return (
                      <tr key={document.id}>
                        <td>
                          <div className="documents-file-cell">
                            <div className="documents-file-icon">
                              ▤
                            </div>

                            <div className="documents-file-info">
                              <strong>{document.titre}</strong>
                              <small>
                                {document.description ||
                                  "Aucune description"}
                              </small>
                            </div>
                          </div>
                        </td>

                        <td>
                          <span className="documents-category">
                            {document.categorie || "AUTRE"}
                          </span>
                        </td>

                        <td>
                          {document.eglise_expediteur_nom ||
                            "Bureau national"}
                        </td>

                        <td>
                          <span className="documents-destination">
                            {document.destinataires_resume
                              ?.map((item) => item.eglise_nom)
                              .filter(Boolean)
                              .join(", ") || "—"}
                          </span>
                        </td>

                        <td>
                          <span
                            className={`documents-status documents-status-${statut}`}
                          >
                            {statut === "confirmé"
                              ? "Réception confirmée"
                              : statut === "lu"
                                ? "Lu"
                                : statut === "non-lu"
                                  ? "Non lu"
                                  : "—"}
                          </span>
                        </td>

                        <td>
                          <div className="actions documents-actions">
                            {document.fichier && (
                              <a
                                className="btn btn-petit btn-secondaire"
                                href={document.fichier}
                                target="_blank"
                                rel="noreferrer"
                              >
                                Ouvrir
                              </a>
                            )}

                            {reception && !reception.lu && (
                              <button
                                type="button"
                                className="btn btn-petit"
                                onClick={() => marquer(document.id)}
                              >
                                Marquer reçu
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>

      {/* FORMULAIRE D'ENVOI */}
      {afficher && (
        <FormulaireDocument
          egliseId={utilisateur?.eglise}
          estNational={estNational}
          eglises={filtrerEglises}
          chargementEglises={chargementEglises}
          recherche={recherche}
          setRecherche={setRecherche}
          onFerme={() => setAfficher(false)}
          onCree={async () => {
            setAfficher(false);
            await charger();
          }}
          erreur={erreur}
          setErreur={setErreur}
        />
      )}
    </div>
  );
}

function FormulaireDocument({
  egliseId,
  estNational,
  eglises,
  chargementEglises,
  recherche,
  setRecherche,
  onFerme,
  onCree,
  erreur,
  setErreur,
}) {
  const [form, setForm] = useState({
    titre: "",
    description: "",
    categorie: "OFFICIEL",
    fichier: null,
    destinataires: [],
  });

  const [envoi, setEnvoi] = useState(false);

  const modifier = (champ, valeur) => {
    setForm((ancien) => ({
      ...ancien,
      [champ]: valeur,
    }));
  };

  const soumettre = async (event) => {
    event.preventDefault();
    setErreur("");

    if (!form.titre.trim()) {
      setErreur("Le titre du document est obligatoire.");
      return;
    }

    if (!form.destinataires.length || !form.fichier) {
      setErreur(
        "Sélectionnez au moins une église et un fichier."
      );
      return;
    }

    const data = new FormData();

    data.append("titre", form.titre.trim());
    data.append("description", form.description);
    data.append("categorie", form.categorie);
    data.append("fichier", form.fichier);

    form.destinataires.forEach((id) => {
      data.append("destinataires", id);
    });

    setEnvoi(true);

    try {
      await client.post("/documents/", data, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      await onCree();
    } catch (err) {
      setErreur(
        err.response?.data?.detail ||
          "Impossible d'envoyer le document."
      );
    } finally {
      setEnvoi(false);
    }
  };

  return (
    <div className="modale-fond" onClick={onFerme}>
      <div
        className="modale large documents-modal"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="documents-modal-header">
          <div>
            <span className="eyebrow">ESPACE DOCUMENTAIRE EESAG</span>
            <h3>Envoyer un document</h3>
            <p>
              Transmettez un fichier aux églises de votre choix.
              Seules les églises sélectionnées pourront y accéder.
            </p>
          </div>

          <button
            type="button"
            className="documents-modal-close"
            onClick={onFerme}
            aria-label="Fermer"
          >
            ×
          </button>
        </div>

        <form onSubmit={soumettre}>
          <div className="form-grid">
            <div className="form-champ">
              <label htmlFor="document-titre">Titre *</label>
              <input
                id="document-titre"
                required
                value={form.titre}
                onChange={(event) =>
                  modifier("titre", event.target.value)
                }
                placeholder="Titre du document"
              />
            </div>

            <div className="form-champ">
              <label htmlFor="document-categorie">Catégorie</label>
              <select
                id="document-categorie"
                value={form.categorie}
                onChange={(event) =>
                  modifier("categorie", event.target.value)
                }
              >
                <option value="OFFICIEL">Officiel</option>
                <option value="ADMINISTRATIF">Administratif</option>
                <option value="RAPPORT">Rapport</option>
                <option value="PROJET">Projet</option>
                <option value="AUTRE">Autre</option>
              </select>
            </div>
          </div>

          <div className="form-champ">
            <label htmlFor="document-description">Description</label>
            <textarea
              id="document-description"
              rows="3"
              value={form.description}
              onChange={(event) =>
                modifier("description", event.target.value)
              }
              placeholder="Description ou informations complémentaires…"
            />
          </div>

          <div className="documents-recipient-heading">
            <div>
              <h4>Églises destinataires</h4>
              <p>
                Sélectionnez les églises qui recevront ce document.
              </p>
            </div>

            <span>
              {form.destinataires.length} sélectionnée(s)
            </span>
          </div>

          <div className="form-champ">
            <label htmlFor="document-recherche-eglise">
              Rechercher une église
            </label>
            <input
              id="document-recherche-eglise"
              placeholder="Nom ou code de l'église…"
              value={recherche}
              onChange={(event) =>
                setRecherche(event.target.value)
              }
            />
          </div>

          <div className="selection-grid documents-selection-grid">
            {chargementEglises ? (
              <div className="empty-state">
                Chargement des églises…
              </div>
            ) : eglises.length ? (
              eglises.map((eglise) => (
                <label
                  className={`selection-card ${
                    form.destinataires.includes(eglise.id)
                      ? "selected"
                      : ""
                  }`}
                  key={eglise.id}
                >
                  <input
                    type="checkbox"
                    checked={form.destinataires.includes(eglise.id)}
                    onChange={(event) =>
                      modifier(
                        "destinataires",
                        event.target.checked
                          ? [...form.destinataires, eglise.id]
                          : form.destinataires.filter(
                              (id) => id !== eglise.id
                            )
                      )
                    }
                  />

                  <div>
                    <b>{eglise.nom}</b>
                    <small>
                      {eglise.code || "—"}
                      {eglise.region_nom
                        ? ` · ${eglise.region_nom}`
                        : ""}
                    </small>
                  </div>
                </label>
              ))
            ) : (
              <div className="empty-state">
                Aucune église trouvée.
              </div>
            )}
          </div>

          <div className="form-champ documents-file-input">
            <label htmlFor="document-fichier">Fichier à transmettre *</label>

            <input
              id="document-fichier"
              required
              type="file"
              accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg"
              onChange={(event) =>
                modifier(
                  "fichier",
                  event.target.files?.[0] || null
                )
              }
            />

            <small>
              Formats acceptés : PDF, Word, Excel et images.
            </small>

            {form.fichier && (
              <p className="documents-selected-file">
                <span>✓</span> {form.fichier.name}
              </p>
            )}
          </div>

          {erreur && (
            <div className="console-error" role="alert">
              {erreur}
            </div>
          )}

          <div className="modal-actions">
            <button
              className="btn"
              type="submit"
              disabled={envoi}
            >
              {envoi ? "Envoi en cours…" : "Envoyer le document"}
            </button>

            <button
              className="btn btn-secondaire"
              type="button"
              onClick={onFerme}
              disabled={envoi}
            >
              Annuler
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
