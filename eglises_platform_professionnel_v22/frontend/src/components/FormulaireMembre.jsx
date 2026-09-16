import { useEffect, useState } from "react";
import client from "../api/client";

export default function FormulaireMembre({ egliseId, onFerme, onCree }) {
  const [erreur, setErreur] = useState("");
  const [apercu, setApercu] = useState("");
  const [departements, setDepartements] = useState([]);
  const [rolesEglise, setRolesEglise] = useState([]);
  const [nouveauDepartement, setNouveauDepartement] = useState("");
  const [nouveauRole, setNouveauRole] = useState("");

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

  useEffect(() => { chargerReferentiels(); }, []);

  const [form, setForm] = useState({
    nom: "", prenom: "", sexe: "H", date_naissance: "", telephone: "", email: "",
    nationalite: "GN", date_bapteme_eau: "", date_bapteme_saint_esprit: "",
    fonction_eglise: "MEMBRE", role: "MEMBRE", eglise: egliseId, departement: "", role_eglise: "",
  });

  const modifier = (champ, valeur) => setForm((f) => ({ ...f, [champ]: valeur }));

  const choisirPhoto = (file) => {
    modifier("photo", file);
    if (!file) { setApercu(""); return; }
    const lecteur = new FileReader();
    lecteur.onload = () => setApercu(String(lecteur.result));
    lecteur.readAsDataURL(file);
  };

  const ajouterDepartement = async () => {
    const nom = nouveauDepartement.trim();
    if (!nom) return;
    try {
      const r = await client.post("/departements/", { nom });
      const d = r.data;
      setDepartements((items) => [...items, d].sort((a, b) => a.nom.localeCompare(b.nom)));
      modifier("departement", d.id);
      setNouveauDepartement("");
    } catch (err) {
      setErreur(err.response?.data?.nom?.[0] || "Impossible d'ajouter le département.");
    }
  };

  const ajouterRole = async () => {
    const nom = nouveauRole.trim();
    if (!nom) return;
    try {
      const r = await client.post("/roles-eglise/", { nom, actif: true });
      const role = r.data;
      setRolesEglise((items) => [...items, role].sort((a, b) => a.nom.localeCompare(b.nom)));
      modifier("role_eglise", role.id);
      setNouveauRole("");
    } catch (err) {
      setErreur(err.response?.data?.nom?.[0] || "Impossible d'ajouter le rôle.");
    }
  };

  const soumettre = async (e) => {
    e.preventDefault();
    setErreur("");
    try {
      const data = new FormData();
      const payload = { ...form, departement: form.departement || "", role_eglise: form.role_eglise || "" };
      Object.entries(payload).forEach(([k, v]) => {
        if (v !== null && v !== undefined) data.append(k, v);
      });
      await client.post("/utilisateurs/", data, { headers: { "Content-Type": "multipart/form-data" } });
      onCree();
    } catch (err) {
      const data = err.response?.data || {};
      setErreur(data.detail || data.telephone?.[0] || data.departement?.[0] || data.role_eglise?.[0] || "Erreur lors de l'ajout du membre.");
    }
  };

  return (
    <div className="modale-fond" onClick={onFerme}>
      <div className="modale" onClick={(e) => e.stopPropagation()}>
        <h3>Ajouter un membre à mon église</h3>
        <p className="sous-titre">Le matricule est généré automatiquement. Le membre reste rattaché à votre église.</p>
        <form onSubmit={soumettre}>
          <div className="form-grid">
            <div className="form-champ"><label>Nom *</label><input required value={form.nom} onChange={(e) => modifier("nom", e.target.value)} /></div>
            <div className="form-champ"><label>Prénom *</label><input required value={form.prenom} onChange={(e) => modifier("prenom", e.target.value)} /></div>
          </div>
          <div className="form-grid">
            <div className="form-champ"><label>Sexe *</label><select value={form.sexe} onChange={(e) => modifier("sexe", e.target.value)}><option value="H">Homme</option><option value="F">Femme</option></select></div>
            <div className="form-champ"><label>Date de naissance</label><input type="date" value={form.date_naissance} onChange={(e) => modifier("date_naissance", e.target.value)} /></div>
          </div>
          <div className="form-grid">
            <div className="form-champ"><label>Téléphone *</label><input required value={form.telephone} onChange={(e) => modifier("telephone", e.target.value)} placeholder="+224..." /></div>
            <div className="form-champ"><label>Email</label><input type="email" value={form.email} onChange={(e) => modifier("email", e.target.value)} /></div>
          </div>

          <div className="form-champ"><label>Nationalité</label><select value={form.nationalite} onChange={(e)=>modifier("nationalite",e.target.value)}><option value="GN">Guinée</option><option value="SN">Sénégal</option><option value="ML">Mali</option><option value="CI">Côte d’Ivoire</option><option value="LR">Libéria</option><option value="SL">Sierra Leone</option><option value="GH">Ghana</option><option value="NG">Nigéria</option><option value="BF">Burkina Faso</option><option value="FR">France</option><option value="US">États-Unis</option><option value="CA">Canada</option><option value="OTHER">Autre</option></select></div>

          <div className="form-grid">
            <div className="form-champ"><label>Baptême d’eau</label><input type="date" value={form.date_bapteme_eau} onChange={(e)=>modifier("date_bapteme_eau",e.target.value)} /></div>
            <div className="form-champ"><label>Baptême du Saint-Esprit</label><input type="date" value={form.date_bapteme_saint_esprit} onChange={(e)=>modifier("date_bapteme_saint_esprit",e.target.value)} /></div>
          </div>

          <div className="form-grid">
            <div className="form-champ">
              <label>Département</label>
              <select value={form.departement} onChange={(e)=>modifier("departement",e.target.value)}>
                <option value="">Aucun</option>
                {departements.map(d => <option key={d.id} value={d.id}>{d.nom}</option>)}
              </select>
              <div className="inline-create">
                <input value={nouveauDepartement} onChange={e=>setNouveauDepartement(e.target.value)} placeholder="Nouveau département" />
                <button type="button" className="btn btn-secondaire" onClick={ajouterDepartement}>＋ Ajouter</button>
              </div>
            </div>

            <div className="form-champ">
              <label>Rôle dans l’église</label>
              <select value={form.role_eglise} onChange={(e)=>modifier("role_eglise",e.target.value)}>
                <option value="">Aucun</option>
                {rolesEglise.map(r => <option key={r.id} value={r.id}>{r.nom}</option>)}
              </select>
              <div className="inline-create">
                <input value={nouveauRole} onChange={e=>setNouveauRole(e.target.value)} placeholder="Nouveau rôle" />
                <button type="button" className="btn btn-secondaire" onClick={ajouterRole}>＋ Ajouter</button>
              </div>
            </div>
          </div>

          <div className="form-champ">
            <label>Photo du membre</label>
            <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(e)=>choisirPhoto(e.target.files?.[0] || null)} />
            <small className="sous-titre">JPG, PNG ou WebP · maximum 5 Mo.</small>
            {apercu && <div className="photo-preview-wrap"><img src={apercu} className="photo-preview" alt="Aperçu du membre" /><span>Aperçu</span></div>}
          </div>

          {erreur && <p className="erreur">{erreur}</p>}
          <div style={{display:"flex",gap:10,marginTop:10}}>
            <button className="btn" type="submit">Enregistrer</button>
            <button className="btn btn-secondaire" type="button" onClick={onFerme}>Annuler</button>
          </div>
        </form>
      </div>
    </div>
  );
}
