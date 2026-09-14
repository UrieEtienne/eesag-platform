import { useEffect, useMemo, useState } from "react";
import client, { mediaUrl } from "../api/client";
import { useAuth } from "../context/AuthContext";

const ANNEE = new Date().getFullYear();
function liste(data) { return data?.results || data || []; }

const TYPES = {
  FEMMES: "♀", JEUNESSE: "★", ENFANTS: "◉", EVANGELISATION: "✦",
  HOMMES: "♂", FAMILLES: "❤", COMMUNICATION: "◌", MUSIQUE: "♪", MISSIONS: "✦"
};

export default function Bureaux() {
  const { estNational, utilisateur, estGestionnaireEglise } = useAuth();
  const [bureaux, setBureaux] = useState([]);
  const [selection, setSelection] = useState(null);
  const [membres, setMembres] = useState([]);
  const [annee, setAnnee] = useState(ANNEE);
  const [erreur, setErreur] = useState("");
  const [message, setMessage] = useState("");
  const [chargement, setChargement] = useState(true);
  const [ajout, setAjout] = useState(false);
  const [form, setForm] = useState({ nom_complet: "", poste: "", photo: null, annee: ANNEE });
  const peutVoirLocaux = estGestionnaireEglise;

  const peutAdministrer = Boolean(selection?.mes_droits?.peut_gerer_membres);

  const chargerBureaux = async () => {
    setChargement(true);
    try {
      const params = estNational || !peutVoirLocaux
        ? { niveau: "NATIONAL", actif: true }
        : { niveau: "LOCAL", eglise: utilisateur?.eglise, actif: true };
      const res = await client.get("/bureaux/", { params });
      const data = liste(res.data);
      setBureaux(data);
      if (!selection && data.length) setSelection(data[0]);
      if (selection) setSelection(data.find((b) => b.id === selection.id) || null);
    } catch (e) {
      setErreur(e.response?.data?.detail || "Impossible de charger les bureaux.");
    } finally { setChargement(false); }
  };

  const chargerMembres = async () => {
    if (!selection) return;
    try {
      const res = await client.get("/bureau-membres-independants/", {
        params: { bureau: selection.id, annee, actif: true }
      });
      setMembres(liste(res.data));
    } catch (e) {
      setMembres([]);
      setErreur(e.response?.data?.detail || "Impossible de charger les membres de ce bureau.");
    }
  };

  useEffect(() => { if (utilisateur) chargerBureaux(); }, [utilisateur, estNational, peutVoirLocaux]);
  useEffect(() => { chargerMembres(); }, [selection, annee]);

  const ajouterMembre = async (e) => {
    e.preventDefault();
    setErreur(""); setMessage("");
    if (!selection) return;
    if (!form.nom_complet.trim() || !form.poste.trim()) {
      setErreur("Le nom complet et le poste sont obligatoires.");
      return;
    }
    try {
      const data = new FormData();
      data.append("bureau", selection.id);
      data.append("nom_complet", form.nom_complet.trim());
      data.append("poste", form.poste.trim());
      data.append("annee", String(annee));
      data.append("actif", "true");
      if (form.photo) data.append("photo", form.photo);
      await client.post("/bureau-membres-independants/", data, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setForm({ nom_complet: "", poste: "", photo: null, annee });
      setAjout(false);
      setMessage("Le membre du bureau a été ajouté sans créer de compte utilisateur.");
      chargerMembres();
    } catch (e) {
      setErreur(e.response?.data?.detail || Object.values(e.response?.data || {}).flat()?.join(" ") || "Ajout refusé.");
    }
  };

  const compteur = useMemo(() => bureaux.reduce((n, b) => n + Number(b.membres_actifs || 0), 0), [bureaux]);

  return (
    <div className="bureaux-page">
      <div className="page-hero bureau-hero">
        <div>
          <span className="eyebrow">GOUVERNANCE EESAG</span>
          <h1>{estNational || !peutVoirLocaux ? "Bureaux nationaux" : "Bureaux internes de l’église"}</h1>
          <p>Choisissez un bureau. Sa composition s’affiche avec les photos et les postes.</p>
        </div>
        <div className="hero-side-stat"><strong>{bureaux.length}</strong><span>structures accessibles</span><small>{compteur} membre(s) actif(s)</small></div>
      </div>

      {erreur && <div className="console-error">{erreur}</div>}
      {message && <div className="console-success">{message}</div>}

      <div className="bureaux-layout">
        <section className="carte bureaux-list-card">
          <div className="section-header">
            <div><span className="eyebrow">BUREAUX</span><h3>Choisir un bureau</h3></div>
          </div>
          {chargement ? <div className="empty-state">Chargement…</div> : <div className="bureau-select-list">
            {bureaux.map((b) => <button key={b.id} className={`bureau-select-row ${selection?.id === b.id ? "selected" : ""}`} onClick={() => setSelection(b)}>
              <span className="bureau-select-icon">{TYPES[b.type_bureau] || "◆"}</span>
              <span><b>{b.nom}</b><small>{b.code}</small></span>
              <strong>{b.membres_actifs || 0}</strong>
            </button>)}
            {!bureaux.length && <div className="empty-state">Aucun bureau accessible.</div>}
          </div>}
        </section>

        <section className="carte bureau-members-card bureau-members-showcase">
          {!selection ? <div className="empty-state large-empty"><span>◆</span><h3>Choisissez un bureau</h3><p>Les membres apparaîtront ici avec leur photo, leur nom complet et leur poste.</p></div> : <>
            <div className="section-header bureau-detail-header">
              <div><span className="eyebrow">{selection.code}</span><h3>{selection.nom}</h3><p>{selection.description || "Composition du bureau."}</p></div>
              <select value={annee} onChange={(e) => setAnnee(Number(e.target.value))} aria-label="Année">
                <option value={ANNEE}>{ANNEE}</option><option value={ANNEE - 1}>{ANNEE - 1}</option><option value={ANNEE + 1}>{ANNEE + 1}</option>
              </select>
            </div>

            {peutAdministrer && <div className="bureau-admin-toolbar">
              <button className="btn" onClick={() => setAjout((v) => !v)}>{ajout ? "Fermer" : "+ Ajouter un membre du bureau"}</button>
              <small>Cette fiche est indépendante des comptes utilisateurs.</small>
            </div>}

            {ajout && peutAdministrer && <form className="bureau-add-form bureau-add-form-large" onSubmit={ajouterMembre}>
              <div className="form-champ"><label>Nom complet</label><input required value={form.nom_complet} onChange={(e) => setForm({ ...form, nom_complet: e.target.value })} placeholder="Ex. Marie K. Diallo" /></div>
              <div className="form-champ"><label>Poste pour {annee}</label><input required value={form.poste} onChange={(e) => setForm({ ...form, poste: e.target.value })} placeholder="Présidente, Secrétaire, Trésorière…" /></div>
              <div className="form-champ"><label>Photo</label><input type="file" accept="image/*" onChange={(e) => setForm({ ...form, photo: e.target.files?.[0] || null })} /></div>
              <button className="btn" type="submit">Enregistrer la composition</button>
            </form>}

            <div className="bureau-members-grid bureau-members-grid-large">
              {membres.map((m) => <article className="bureau-member-card bureau-member-card-large" key={m.id}>
                <div className="bureau-member-photo bureau-member-photo-large">
                  {m.photo_url || m.photo ? <img src={mediaUrl(m.photo_url || m.photo)} alt={m.nom_complet} /> : <img src="/assets/logo_eesag.jpg" alt="EESAG" />}
                </div>
                <div className="bureau-member-info-large">
                  <h4>{m.nom_complet}</h4>
                  <p>{m.poste}</p>
                  <small>Mandat {m.annee}</small>
                </div>
              </article>)}
              {!membres.length && <div className="empty-state">Aucun membre enregistré pour {annee}.</div>}
            </div>
          </>}
        </section>
      </div>
    </div>
  );
}
