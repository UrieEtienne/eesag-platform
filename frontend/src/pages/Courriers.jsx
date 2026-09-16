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

      {afficherFormulaire && <FormulaireCourrier onFerme={() => setAfficherFormulaire(false)} onCree={() => { setAfficherFormulaire(false); charger(); }} />}
    </div>
  );
}

function FormulaireCourrier({ onFerme, onCree }) {
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
    objet: "Recommandation de déplacement",
    contenu: "",
    fichier_word: null,
  });

  useEffect(() => {
    client.get("/eglises/").then((res) => setEglises(liste(res.data))).catch(() => setEglises([]));
  }, []);

  useEffect(() => {
    if (terme.length < 2) { setMembresTrouves([]); return; }
    const timer = setTimeout(() => {
      client.get("/membres/recherche/", { params: { q: terme } })
        .then((res) => setMembresTrouves(liste(res.data)))
        .catch(() => setMembresTrouves([]));
    }, 300);
    return () => clearTimeout(timer);
  }, [terme]);

  const modifier = (champ, valeur) => setForm((f) => ({ ...f, [champ]: valeur }));
  const fichierNom = useMemo(() => form.fichier_word?.name || "Aucun fichier Word sélectionné", [form.fichier_word]);

  const apercu = async () => {
    setErreur("");
    setBusy(true);
    try {
      const fd = new FormData();
      Object.entries(form).forEach(([k, v]) => { if (v !== null && v !== undefined && v !== "") fd.append(k, v); });
      const { data } = await client.post("/courriers/apercu/", fd, { headers: { "Content-Type": "multipart/form-data" } });
      setPreview(data);
    } catch (err) {
      setErreur(err.response?.data?.detail || "Impossible de générer l’aperçu.");
    } finally { setBusy(false); }
  };

  const envoyer = async () => {
    if (!preview) return;
    setErreur("");
    setBusy(true);
    try {
      const fd = new FormData();
      Object.entries(form).forEach(([k, v]) => { if (v !== null && v !== undefined && v !== "") fd.append(k, v); });
      await client.post("/courriers/", fd, { headers: { "Content-Type": "multipart/form-data" } });
      onCree();
    } catch (err) {
      setErreur(err.response?.data?.detail || "Erreur lors de l’envoi du courrier.");
    } finally { setBusy(false); }
  };

  return (
    <div className="modale-fond" onClick={onFerme}>
      <div className="modale courrier-editor" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div><span className="eyebrow">PASTEUR</span><h3>Lettre de recommandation</h3></div>
          <button className="modal-close" onClick={onFerme}>×</button>
        </div>

        <div className="editor-grid">
          <div>
            <div className="form-champ">
              <label>Membre concerné *</label>
              <input value={terme} onChange={(e) => setTerme(e.target.value)} placeholder="Nom, prénom ou identifiant…" />
              {membresTrouves.length > 0 && (
                <select size={5} value={form.membre_concerne} onChange={(e) => modifier("membre_concerne", e.target.value)}>
                  {membresTrouves.map((m) => <option key={m.id} value={m.id}>{m.nom_complet} — {m.identifiant}</option>)}
                </select>
              )}
              {membreSelectionne && (
                <div className="member-selection-card">
                  <div className="member-selection-head">
                    <div>
                      <span className="eyebrow">FICHE DU MEMBRE</span>
                      <strong>{membreSelectionne.nom_complet}</strong>
                    </div>
                    <span className="status-chip ok">Sélectionné</span>
                  </div>
                  <div className="member-selection-grid">
                    <span><b>Identifiant</b>{membreSelectionne.identifiant}</span>
                    <span><b>Fonction</b>{membreSelectionne.fonction_eglise || "Membre"}</span>
                    <span><b>Téléphone</b>{membreSelectionne.telephone || "—"}</span>
                    <span><b>Église</b>{membreSelectionne.eglise_nom || utilisateur?.eglise_nom || "—"}</span>
                  </div>
                  <small>Les autres informations disponibles seront reprises automatiquement dans l'aperçu et le document.</small>
                </div>
              )}
            </div>

            <div className="form-champ">
              <label>Localité / église destinataire *</label>
              <select required value={form.eglise_destinataire} onChange={(e) => { modifier("eglise_destinataire", e.target.value); setPreview(null); }}>
                <option value="">-- Choisir l’église --</option>
                {eglises.map((eg) => <option key={eg.id} value={eg.id}>{eg.nom} ({eg.code})</option>)}
              </select>
            </div>

            <div className="form-champ"><label>Objet *</label><input required value={form.objet} onChange={(e) => modifier("objet", e.target.value)} /></div>

            <div className="form-champ">
              <label>Document Word préparé, signé et cacheté</label>
              <input type="file" accept=".doc,.docx" onChange={(e) => modifier("fichier_word", e.target.files?.[0] || null)} />
              <small className="helper-text">Le système remplit automatiquement les champs Word disponibles : {"{{NOM_COMPLET}}"}, {"{{IDENTIFIANT}}"}, {"{{TELEPHONE}}"}, {"{{EMAIL}}"}, {"{{FONCTION}}"}, {"{{ROLE_EGLISE}}"}, {"{{DEPARTEMENT}}"}, {"{{EGLISE}}"}, {"{{CODE_EGLISE}}"}, {"{{EGLISE_DESTINATION}}"}, {"{{CODE_EGLISE_DESTINATION}}"}, {"{{DATE}}"}.</small>
              <small className="helper-text">{fichierNom}</small>
            </div>

            <div className="form-champ">
              <label>Autres phrases du pasteur</label>
              <textarea rows={8} value={form.contenu} onChange={(e) => modifier("contenu", e.target.value)} placeholder="Ajoutez vos phrases, le contexte du déplacement et les informations utiles…" />
            </div>

            {erreur && <p className="erreur">{erreur}</p>}

            <div className="modal-actions">
              <button className="btn btn-secondaire" type="button" onClick={onFerme}>Annuler</button>
              <button className="btn" type="button" onClick={apercu} disabled={busy}>Aperçu avant envoi</button>
            </div>
          </div>

          <div className="preview-pane">
            <span className="eyebrow">APERÇU</span>
            {!preview ? (
              <div className="preview-empty"><span>▣</span><p>Remplissez les informations puis cliquez sur <b>Aperçu avant envoi</b>.</p></div>
            ) : (
              <>
                <div className="preview-paper">
                  <div className="preview-brand">EESAG</div>
                  <h4>{preview.objet}</h4>
                  <div className="preview-identity-grid">
                    <p><b>Membre</b>{preview.membre_nom}</p>
                    <p><b>Identifiant</b>{preview.membre_identifiant}</p>
                    <p><b>Fonction</b>{preview.fonction || "Membre"}</p>
                    <p><b>Département</b>{preview.departement || "—"}</p>
                    <p><b>Téléphone</b>{preview.telephone || "—"}</p>
                    <p><b>Nationalité</b>{preview.nationalite || "—"}</p>
                  </div>
                  <hr />
                  <p><b>Départ :</b> {preview.eglise_origine} ({preview.code_origine})</p>
                  <p><b>Destination :</b> {preview.eglise_destinataire} ({preview.code_destination})</p>
                  <p><b>Localité :</b> {preview.localite_destination || "—"}</p>
                  <hr />
                  <p className="preview-text">{preview.contenu}</p>
                </div>
                <div className="preview-actions">
                  <span className="preview-confirmation">Relisez le document avant l'envoi définitif.</span>
                  <button className="btn" type="button" onClick={envoyer} disabled={busy}>Valider et envoyer</button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
