import { useEffect, useMemo, useState } from "react";
import client from "../api/client";
import { mediaUrl } from "../api/client";
import { useAuth } from "../context/AuthContext";

function liste(data) { return data?.results || data || []; }

export default function Courriers() {
  const { utilisateur, estCoordinateur } = useAuth();
  const estPasteur = utilisateur?.role === "PASTEUR";
  const peutCourrier = estPasteur || estCoordinateur;
  const [courriers, setCourriers] = useState([]);
  const [afficherFormulaire, setAfficherFormulaire] = useState(false);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState("");

  const charger = () => {
    setChargement(true);
    client.get("/courriers/")
      .then((res) => setCourriers(liste(res.data)))
      .catch((err) => setErreur(err.response?.data?.detail || "Impossible de charger les courriers."))
      .finally(() => setChargement(false));
  };
  useEffect(charger, []);

  const telecharger = async (courrier) => {
    try {
      const res = await client.get(`/courriers/${courrier.id}/telecharger/`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const lien = document.createElement("a");
      lien.href = url;
      lien.download = `${courrier.numero_reference.replace(/\//g, "-")}.pdf`;
      lien.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setErreur(err.response?.data?.detail || "Téléchargement impossible.");
    }
  };

  const marquerRecu = async (courrier) => {
    try {
      await client.post(`/courriers/${courrier.id}/marquer_recu/`);
      charger();
    } catch (err) {
      setErreur(err.response?.data?.detail || "Vous n'êtes pas autorisé à réceptionner ce courrier.");
    }
  };

  return (
    <div className="page-shell">
      <div className="page-hero">
        <div>
          <span className="eyebrow">COURRIERS EESAG</span>
          <h1>Correspondances officielles</h1>
          <p>
            Les lettres de recommandation sont préparées par le pasteur, personnalisées,
            prévisualisées puis envoyées à l’église de destination.
          </p>
        </div>
        {estPasteur && <button className="btn" onClick={() => setAfficherFormulaire(true)}>+ Nouvelle recommandation</button>}
      </div>

      {!estPasteur && !estCoordinateur && (
        <div className="console-error">La gestion des courriers est réservée au pasteur de l’église.</div>
      )}
      {erreur && <div className="console-error">{erreur}</div>}

      <div className="carte">
        <div className="section-header">
          <div>
            <span className="eyebrow">BOÎTE OFFICIELLE</span>
            <h3>Courriers envoyés et reçus</h3>
          </div>
          <span className="scope-badge">{utilisateur?.eglise_nom || (estCoordinateur ? "Coordination nationale" : "—")}</span>
        </div>

        {chargement ? <div className="empty-state">Chargement…</div> : (
          <div className="table-responsive">
            <table>
              <thead>
                <tr><th>Référence</th><th>Type</th><th>Objet</th><th>Destination</th><th>Date</th><th>État</th><th></th></tr>
              </thead>
              <tbody>
                {courriers.map((c) => (
                  <tr key={c.id}>
                    <td>{c.numero_reference}</td>
                    <td>{c.type_courrier}</td>
                    <td>{c.objet}</td>
                    <td>{c.eglise_destinataire_nom || "—"}</td>
                    <td>{c.date_emission}</td>
                    <td><span className={`status-chip ${c.lu ? "ok" : "pending"}`}>{c.lu ? "Reçu" : "Nouveau"}</span></td>
                    <td>
                      <div className="actions">
                        <button className="btn btn-petit btn-secondaire" onClick={() => telecharger(c)}>PDF</button>
                        {c.fichier_word && <a className="btn btn-petit" href={c.fichier_word} target="_blank" rel="noreferrer">Word</a>}
                        {!c.lu && estPasteur && utilisateur?.eglise_nom && <button className="btn btn-petit" onClick={() => marquerRecu(c)}>Réceptionner</button>}
                      </div>
                    </td>
                  </tr>
                ))}
                {!courriers.length && <tr><td colSpan={7} style={{ textAlign: "center", color: "#64748b", padding: 28 }}>Aucun courrier dans votre périmètre.</td></tr>}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {afficherFormulaire && (
          <FormulaireCourrier
            utilisateur={utilisateur}
            onFerme={() => setAfficherFormulaire(false)}
            onCree={() => {
                  setAfficherFormulaire(false);
                  charger();
            }}
          />
      )}
          </div>
        );
      }

function FormulaireCourrier({ utilisateur, onFerme, onCree }) {
  const [eglises, setEglises] = useState([]);
  const [terme, setTerme] = useState("");
  const [membresTrouves, setMembresTrouves] = useState([]);
  const [membreSelectionne, setMembreSelectionne] = useState(null);
  const [preview, setPreview] = useState(null);
  const [erreur, setErreur] = useState("");
  const [busy, setBusy] = useState(false);

  const [form, setForm] = useState({
    type_courrier: "RECOMMANDATION",
    eglise_destinataire: "",
    membre_concerne: "",
    objet: "Lettre de recommandation",
    contenu: "",
    fichier_word: null,
  });

  const [details, setDetails] = useState({
    motif_depart: "",
    date_bapteme: "",
    lieu_bapteme: "",
    situation_matrimoniale: "",
    fonction_eglise: "",
    stabilite: "",
    fidelite: "",
    soumission: "",
    observations: "",
  });

  const listeLocale = (data) =>
    Array.isArray(data) ? data : data?.results || data?.data || [];

  const modifier = (champ, valeur) => {
    setForm((ancien) => ({ ...ancien, [champ]: valeur }));
    setPreview(null);
    setErreur("");
  };

  const modifierDetail = (champ, valeur) => {
    setDetails((ancien) => ({ ...ancien, [champ]: valeur }));
    setPreview(null);
    setErreur("");
  };

  const valeurMembre = (...valeurs) =>
    valeurs.find((valeur) => valeur !== null &&
      valeur !== undefined && String(valeur).trim() !== "") || "";

  const nomComplet = (membre) =>
    [membre?.prenom, membre?.nom].filter(Boolean).join(" ") ||
    membre?.nom_complet ||
    membre?.identifiant ||
    "Membre";

  const egliseOrigine = valeurMembre(
    membreSelectionne?.eglise_nom,
    membreSelectionne?.eglise?.nom,
    membreSelectionne?.nom_eglise,
    utilisateur?.eglise_nom,
    utilisateur?.eglise?.nom
  );

  const zoneOrigine = valeurMembre(
    membreSelectionne?.zone_nom,
    membreSelectionne?.eglise?.zone_nom,
    membreSelectionne?.eglise?.region_nom
  );

  const telephoneMembre = valeurMembre(
    membreSelectionne?.telephone,
    membreSelectionne?.numero_telephone
  );

  const emailMembre = valeurMembre(membreSelectionne?.email);

  const nomFichier =
    form.fichier_word?.name || "Aucun document Word sélectionné";

  useEffect(() => {
    let actif = true;

    client
      .get("/eglises/")
      .then((res) => {
        if (actif) setEglises(listeLocale(res.data));
      })
      .catch(() => {
        if (actif) {
          setErreur("Impossible de charger les églises de destination.");
        }
      });

    return () => {
      actif = false;
    };
  }, []);

  useEffect(() => {
    const recherche = terme.trim();

    if (recherche.length < 2) {
      setMembresTrouves([]);
      return undefined;
    }

    let actif = true;

    const timer = setTimeout(() => {
      client
        .get("/membres/recherche/", { params: { q: recherche } })
        .then((res) => {
          if (actif) setMembresTrouves(listeLocale(res.data));
        })
        .catch(() => {
          if (actif) setMembresTrouves([]);
        });
    }, 300);

    return () => {
      actif = false;
      clearTimeout(timer);
    };
  }, [terme]);

  const selectionnerMembre = (event) => {
    const id = event.target.value;

    const membre = membresTrouves.find(
      (element) => String(element.id) === String(id)
    );

    setMembreSelectionne(membre || null);
    setPreview(null);
    setErreur("");

    setForm((ancien) => ({
      ...ancien,
      membre_concerne: id,
    }));

    if (!membre) return;

    setTerme(nomComplet(membre));

    setDetails((ancien) => ({
      ...ancien,
      date_bapteme: valeurMembre(
        membre.date_bapteme_eau,
        membre.date_bapteme
      ),
      lieu_bapteme: valeurMembre(
        membre.lieu_bapteme,
        membre.lieu_bapteme_eau
      ),
      situation_matrimoniale: valeurMembre(
        membre.situation_matrimoniale,
        membre.situation_familiale
      ),
      fonction_eglise: valeurMembre(
        membre.fonction_eglise,
        membre.fonction,
        membre.role_eglise
      ),
    }));
  };

  const construireContenu = () => {
    const engagement = [
      ["Stabilité spirituelle", details.stabilite],
      ["Fidélité", details.fidelite],
      ["Soumission", details.soumission],
    ]
      .filter(([, valeur]) => valeur)
      .map(([titre, valeur]) => `${titre} : ${valeur}`)
      .join("\n");

    return [
      "LETTRE DE RECOMMANDATION",
      "",
      "À l'attention du pasteur et des responsables de l'église destinataire,",
      "",
      "Que la grâce et la paix de Dieu le Père et de notre Seigneur Jésus-Christ soient avec vous.",
      "",
      `Nous, responsables de l'église ${egliseOrigine || "d'origine"}, avons le plaisir de recommander à votre communion fraternelle le membre suivant :`,
      "",
      `Nom complet : ${nomComplet(membreSelectionne)}`,
      `Identifiant EESAG : ${membreSelectionne?.identifiant || ""}`,
      `Téléphone : ${telephoneMembre || "Non renseigné"}`,
      `Adresse e-mail : ${emailMembre || "Non renseignée"}`,
      `Église d'origine : ${egliseOrigine || "Non renseignée"}`,
      `Zone d'origine : ${zoneOrigine || "Non renseignée"}`,
      `Fonction dans l'église : ${details.fonction_eglise || "Non renseignée"}`,
      `Baptême : ${details.date_bapteme || "Non renseigné"}`,
      `Lieu du baptême : ${details.lieu_bapteme || "Non renseigné"}`,
      `Situation matrimoniale : ${details.situation_matrimoniale || "Non renseignée"}`,
      "",
      "MOTIF DU DÉPLACEMENT",
      details.motif_depart || "À compléter par le pasteur.",
      "",
      "ENGAGEMENT ET APPRÉCIATION PASTORALE",
      engagement || "Appréciation pastorale à compléter.",
      "",
      "OBSERVATIONS COMPLÉMENTAIRES",
      details.observations || "Aucune observation complémentaire.",
      "",
      "Nous vous prions de bien vouloir accueillir ce membre dans un esprit de communion fraternelle.",
      "",
      "Fait pour servir et valoir ce que de droit.",
      "",
      `Pasteur de l'église d'origine : ${utilisateur?.prenom || ""} ${utilisateur?.nom || ""}`.trim(),
    ].join("\n");
  };

  const creerFormData = () => {
    const fd = new FormData();

    fd.append("type_courrier", form.type_courrier);
    fd.append("eglise_destinataire", form.eglise_destinataire);
    fd.append("membre_concerne", form.membre_concerne);
    fd.append("objet", form.objet.trim());
    fd.append("contenu", construireContenu());

    if (form.fichier_word) {
      fd.append("fichier_word", form.fichier_word);
    }

    return fd;
  };

  const apercu = async () => {
    setErreur("");
    setPreview(null);

    if (!form.membre_concerne || !membreSelectionne) {
      setErreur("Sélectionne un membre dans les résultats de recherche.");
      return;
    }

    if (!form.eglise_destinataire) {
      setErreur("Sélectionne l'église de destination.");
      return;
    }

    if (!form.objet.trim() || !details.motif_depart.trim()) {
      setErreur("Renseigne l'objet et le motif du déplacement.");
      return;
    }

    setBusy(true);

    try {
      const { data } = await client.post(
        "/courriers/apercu/",
        creerFormData()
      );

      setPreview(data);
    } catch (err) {
      const data = err.response?.data;
      setErreur(
        data?.detail ||
          (typeof data === "object"
            ? Object.entries(data || {})
                .map(([champ, valeur]) =>
                  `${champ} : ${Array.isArray(valeur) ? valeur.join(", ") : valeur}`
                )
                .join(" | ")
            : null) ||
          "Impossible de générer l'aperçu de la lettre."
      );
    } finally {
      setBusy(false);
    }
  };

  const envoyer = async () => {
    if (!preview || !membreSelectionne) {
      setErreur("Génère d'abord l'aperçu de la lettre.");
      return;
    }

    setErreur("");
    setBusy(true);

    try {
      await client.post("/courriers/", creerFormData());
      onCree();
    } catch (err) {
      const data = err.response?.data;
      setErreur(
        data?.detail ||
          (typeof data === "object"
            ? Object.entries(data || {})
                .map(([champ, valeur]) =>
                  `${champ} : ${Array.isArray(valeur) ? valeur.join(", ") : valeur}`
                )
                .join(" | ")
            : null) ||
          "L'envoi de la lettre a échoué."
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="modale-fond" onClick={onFerme}>
      <div
        className="modale courrier-editor"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="modal-header">
          <div>
            <span className="eyebrow">EESAG · PASTEUR</span>
            <h3>Nouvelle lettre de recommandation</h3>
          </div>
          <button
            type="button"
            className="modal-close"
            onClick={onFerme}
            aria-label="Fermer"
          >
            ×
          </button>
        </div>

        <div className="editor-grid">
          <div>
            <div className="form-champ">
              <label htmlFor="recherche-membre">Rechercher un membre *</label>
              <input
                id="recherche-membre"
                value={terme}
                onChange={(event) => {
                  setTerme(event.target.value);
                  setMembreSelectionne(null);
                  setForm((ancien) => ({
                    ...ancien,
                    membre_concerne: "",
                  }));
                  setPreview(null);
                }}
                placeholder="Nom, prénom ou identifiant…"
                autoComplete="off"
              />

              {membresTrouves.length > 0 && (
                <select
                  aria-label="Choisir le membre"
                  size={Math.min(membresTrouves.length, 5)}
                  value={form.membre_concerne}
                  onChange={selectionnerMembre}
                >
                  <option value="">— Sélectionner le membre —</option>
                  {membresTrouves.map((membre) => (
                    <option key={membre.id} value={membre.id}>
                      {nomComplet(membre)} — {membre.identifiant || membre.id}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {membreSelectionne && (
              <section className="carte mb-3">
                <div className="section-header">
                  <div>
                    <span className="eyebrow">FICHE DU MEMBRE</span>
                    <h4>{nomComplet(membreSelectionne)}</h4>
                  </div>
                  <span className="status-chip ok">Sélectionné</span>
                </div>

                <div className="p-3">
                  <p><strong>Identifiant :</strong> {membreSelectionne.identifiant || "—"}</p>
                  <p><strong>Téléphone :</strong> {telephoneMembre || "—"}</p>
                  <p><strong>E-mail :</strong> {emailMembre || "—"}</p>
                  <p><strong>Église d'origine :</strong> {egliseOrigine || "—"}</p>
                  <p className="mb-0"><strong>Zone :</strong> {zoneOrigine || "À compléter"}</p>
                </div>
              </section>
            )}

            <div className="form-champ">
              <label htmlFor="eglise-destination">Église de destination *</label>
              <select
                id="eglise-destination"
                required
                value={form.eglise_destinataire}
                onChange={(event) =>
                  modifier("eglise_destinataire", event.target.value)
                }
              >
                <option value="">— Choisir l'église —</option>
                {eglises.map((eglise) => (
                  <option key={eglise.id} value={eglise.id}>
                    {eglise.nom} {eglise.code ? `(${eglise.code})` : ""}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-champ">
              <label htmlFor="objet-lettre">Objet de la lettre *</label>
              <input
                id="objet-lettre"
                required
                value={form.objet}
                onChange={(event) => modifier("objet", event.target.value)}
              />
            </div>

            <div className="form-champ">
              <label htmlFor="motif-depart">Motif du déplacement *</label>
              <textarea
                id="motif-depart"
                rows={3}
                required
                value={details.motif_depart}
                onChange={(event) =>
                  modifierDetail("motif_depart", event.target.value)
                }
                placeholder="Ex. : mutation professionnelle, déménagement, mariage, études…"
              />
            </div>

            <h4 className="mt-4">Informations complémentaires</h4>

            <div className="form-champ">
              <label htmlFor="date-bapteme">Date du baptême d'eau</label>
              <input
                id="date-bapteme"
                type="date"
                value={details.date_bapteme}
                onChange={(event) =>
                  modifierDetail("date_bapteme", event.target.value)
                }
              />
            </div>

            <div className="form-champ">
              <label htmlFor="lieu-bapteme">Lieu du baptême</label>
              <input
                id="lieu-bapteme"
                value={details.lieu_bapteme}
                onChange={(event) =>
                  modifierDetail("lieu_bapteme", event.target.value)
                }
                placeholder="Lieu du baptême, si connu"
              />
            </div>

            <div className="form-champ">
              <label htmlFor="situation-matrimoniale">Situation matrimoniale</label>
              <select
                id="situation-matrimoniale"
                value={details.situation_matrimoniale}
                onChange={(event) =>
                  modifierDetail("situation_matrimoniale", event.target.value)
                }
              >
                <option value="">— Non renseignée —</option>
                <option value="Célibataire">Célibataire</option>
                <option value="Marié(e)">Marié(e)</option>
                <option value="Veuf / Veuve">Veuf / Veuve</option>
                <option value="Divorcé(e)">Divorcé(e)</option>
                <option value="Autre">Autre</option>
              </select>
            </div>

            <div className="form-champ">
              <label htmlFor="fonction-eglise">Fonction dans l'église</label>
              <input
                id="fonction-eglise"
                value={details.fonction_eglise}
                onChange={(event) =>
                  modifierDetail("fonction_eglise", event.target.value)
                }
                placeholder="Ex. : membre, moniteur, responsable de département…"
              />
            </div>

            <h4 className="mt-4">Appréciation pastorale</h4>
            <p className="helper-text">
              Ces appréciations sont à compléter par le pasteur selon
              l'engagement réel du membre.
            </p>

            {[
              ["stabilite", "Stabilité spirituelle"],
              ["fidelite", "Fidélité"],
              ["soumission", "Soumission et respect de l'encadrement"],
            ].map(([champ, titre]) => (
              <div className="form-champ" key={champ}>
                <label htmlFor={`engagement-${champ}`}>{titre}</label>
                <select
                  id={`engagement-${champ}`}
                  value={details[champ]}
                  onChange={(event) =>
                    modifierDetail(champ, event.target.value)
                  }
                >
                  <option value="">— À évaluer —</option>
                  <option value="Satisfaisant">Satisfaisant</option>
                  <option value="À améliorer">À améliorer</option>
                  <option value="Non évalué">Non évalué</option>
                </select>
              </div>
            ))}

            <div className="form-champ">
              <label htmlFor="observations-pastorales">
                Observations complémentaires
              </label>
              <textarea
                id="observations-pastorales"
                rows={4}
                value={details.observations}
                onChange={(event) =>
                  modifierDetail("observations", event.target.value)
                }
                placeholder="Engagement dans l'église, responsabilités, appréciation pastorale…"
              />
            </div>

            <div className="form-champ">
              <label htmlFor="fichier-word">
                Modèle Word signé et cacheté (facultatif)
              </label>
              <input
                id="fichier-word"
                type="file"
                accept=".doc,.docx"
                onChange={(event) => {
                  modifier("fichier_word", event.target.files?.[0] || null);
                }}
              />
              <small className="helper-text">{nomFichier}</small>
            </div>

            {erreur && (
              <div className="console-error" role="alert">
                {erreur}
              </div>
            )}

            <div className="modal-actions">
              <button
                type="button"
                className="btn btn-secondaire"
                onClick={onFerme}
                disabled={busy}
              >
                Annuler
              </button>
              <button
                type="button"
                className="btn"
                onClick={apercu}
                disabled={busy || !membreSelectionne}
              >
                {busy ? "Préparation…" : "Générer l'aperçu"}
              </button>
            </div>
          </div>

          <div className="preview-pane">
            <span className="eyebrow">APERÇU DE LA LETTRE</span>

            {!preview ? (
              <div className="preview-empty">
                <span>▣</span>
                <p>
                  Sélectionne un membre, complète les informations nécessaires,
                  puis génère l'aperçu.
                </p>
              </div>
            ) : (
              <>
                <div className="preview-paper">
                  <div className="preview-brand">EESAG</div>
                  <h4>{preview.objet || form.objet}</h4>
                  <p><strong>Membre :</strong> {nomComplet(membreSelectionne)}</p>
                  <p><strong>Identifiant :</strong> {membreSelectionne?.identifiant || "—"}</p>
                  <p><strong>Église d'origine :</strong> {egliseOrigine || "—"}</p>
                  <p>
                    <strong>Église destinataire :</strong>{" "}
                    {preview.eglise_destinataire || eglises.find(
                      (eglise) => String(eglise.id) === form.eglise_destinataire
                    )?.nom || "—"}
                  </p>
                  <hr />
                  <div
                    className="preview-text"
                    style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}
                  >
                    {preview.contenu || construireContenu()}
                  </div>
                </div>

                <button
                  type="button"
                  className="btn btn-secondaire w-100 mb-2"
                  onClick={apercu}
                  disabled={busy}
                >
                  Actualiser l'aperçu
                </button>

                <button
                  type="button"
                  className="btn w-100"
                  onClick={envoyer}
                  disabled={busy}
                >
                  {busy ? "Envoi en cours…" : "Valider et envoyer la lettre"}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}