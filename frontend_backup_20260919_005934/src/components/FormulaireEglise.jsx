import { useEffect, useState } from "react";
import client from "../api/client";

const initial = {
  nom: "",
  religion: "",
  region: "",
  prefecture: "",
  district: "",
  commune: "",
  adresse_precise: "",
  telephone: "",
  email: "",
  date_creation: "",
  responsable_nom: "",
  responsable_telephone: "",
  responsable_email: "",
};

export default function FormulaireEglise({ onFerme, onCree }) {
  const [religions, setReligions] = useState([]);
  const [regions, setRegions] = useState([]);
  const [prefectures, setPrefectures] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [communes, setCommunes] = useState([]);
  const [erreur, setErreur] = useState("");
  const [resultat, setResultat] = useState(null);
  const [form, setForm] = useState(initial);

  useEffect(() => {
    Promise.all([client.get("/religions/"), client.get("/geo/regions/")])
      .then(([religionsResponse, regionsResponse]) => {
        setReligions(religionsResponse.data.results || religionsResponse.data || []);
        setRegions(regionsResponse.data.results || regionsResponse.data || []);
      })
      .catch(() => {
        setReligions([]);
        setRegions([]);
      });
  }, []);

  useEffect(() => {
    if (!form.region) {
      setPrefectures([]);
      return;
    }
    client.get("/geo/prefectures/", { params: { region: form.region } })
      .then((response) => setPrefectures(response.data.results || response.data || []))
      .catch(() => setPrefectures([]));
  }, [form.region]);

  useEffect(() => {
    if (!form.prefecture) {
      setDistricts([]);
      return;
    }
    client.get("/geo/districts/", { params: { prefecture: form.prefecture } })
      .then((response) => setDistricts(response.data.results || response.data || []))
      .catch(() => setDistricts([]));
  }, [form.prefecture]);

  useEffect(() => {
    if (!form.district) {
      setCommunes([]);
      return;
    }
    client.get("/geo/communes/", { params: { district: form.district } })
      .then((response) => setCommunes(response.data.results || response.data || []))
      .catch(() => setCommunes([]));
  }, [form.district]);

  const setField = (field, value) => setForm((current) => ({ ...current, [field]: value }));

  const normaliserNumero = (value) => {
    const raw = String(value || "").trim().replace(/[\s().-]/g, "");
    if (raw.startsWith("00")) return "+" + raw.slice(2);
    if (raw.startsWith("+")) return "+" + raw.slice(1).replace(/\D/g, "");
    const digits = raw.replace(/\D/g, "");
    if (digits.length === 9 && digits.startsWith("6")) return "+224" + digits;
    if (digits.startsWith("224") && digits.length === 12) return "+" + digits;
    return raw;
  };

  const soumettre = async (event) => {
    event.preventDefault();
    setErreur("");
    const payload = {
      ...form,
      telephone: normaliserNumero(form.telephone),
      responsable_telephone: normaliserNumero(form.responsable_telephone),
      plateforme_active: false,
    };
    try {
      const response = await client.post("/eglises/", payload);
      setResultat(response.data);
    } catch (error) {
      const data = error.response?.data;
      const messages = Object.values(data || {}).flat().filter(Boolean);
      setErreur(
        typeof data === "string"
          ? data
          : data?.detail || messages.join(" ") || "Impossible de créer l'église."
      );
    }
  };

  if (resultat) {
    return (
      <div className="modale-fond">
        <div className="modale">
          <div className="success-box">
            <div className="success-icon">✓</div>
            <h3>Église enregistrée</h3>
            <p>{resultat.nom} a été ajoutée au réseau EESAG.</p>
            <div className="credential-box">
              <small>Code de l'église</small>
              <strong>{resultat.code || "—"}</strong>
              <small>Accès à la plateforme</small>
              <strong>À ACTIVER PAR LE BUREAU NATIONAL</strong>
              <small>Compte administrateur</small>
              <strong>Création uniquement dans Django Admin</strong>
            </div>
            <button
              className="btn"
              onClick={() => {
                onCree?.(resultat);
                onFerme();
              }}
            >
              Fermer
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="modale-fond" onClick={onFerme}>
      <div className="modale xl" onClick={(event) => event.stopPropagation()}>
        <div className="section-header">
          <div>
            <span className="eyebrow">ENREGISTREMENT NATIONAL</span>
            <h3>Créer une nouvelle église</h3>
            <p>Cette étape enregistre uniquement l'église. Le premier administrateur local est créé ensuite dans Django Admin.</p>
          </div>
        </div>

        <div className="activation-note">
          <b>Workflow sécurisé</b>
          <small>
            1. Création de l'église · 2. Création du compte administrateur dans Django Admin · 3. Le compte reste bloqué · 4. Le Bureau national active l'église et l'accès du compte.
          </small>
        </div>

        <form onSubmit={soumettre}>
          <div className="form-section">
            <h4>Informations de l'église</h4>
            <div className="form-grid">
              <div className="form-champ"><label>Nom *</label><input required value={form.nom} onChange={(e) => setField("nom", e.target.value)} /></div>
              <div className="form-champ"><label>Région *</label><select required value={form.region} onChange={(e) => { setField("region", e.target.value); setField("prefecture", ""); setField("district", ""); setField("commune", ""); }}><option value="">Choisir</option>{regions.map((item) => <option key={item.id} value={item.id}>{item.nom}</option>)}</select></div>
              <div className="form-champ"><label>Préfecture *</label><select required disabled={!form.region} value={form.prefecture} onChange={(e) => { setField("prefecture", e.target.value); setField("district", ""); setField("commune", ""); }}><option value="">Choisir</option>{prefectures.map((item) => <option key={item.id} value={item.id}>{item.nom}</option>)}</select></div>
              <div className="form-champ"><label>District *</label><select required disabled={!form.prefecture} value={form.district} onChange={(e) => { setField("district", e.target.value); setField("commune", ""); }}><option value="">Choisir</option>{districts.map((item) => <option key={item.id} value={item.id}>{item.nom}</option>)}</select></div>
              <div className="form-champ"><label>Commune</label><select disabled={!form.district} value={form.commune} onChange={(e) => setField("commune", e.target.value)}><option value="">Choisir</option>{communes.map((item) => <option key={item.id} value={item.id}>{item.nom}</option>)}</select></div>
              <div className="form-champ"><label>Téléphone</label><input value={form.telephone} onChange={(e) => setField("telephone", e.target.value)} placeholder="+224..." /></div>
              <div className="form-champ"><label>Email</label><input type="email" value={form.email} onChange={(e) => setField("email", e.target.value)} /></div>
            </div>
            <div className="form-champ"><label>Adresse précise</label><input value={form.adresse_precise} onChange={(e) => setField("adresse_precise", e.target.value)} /></div>
            <div className="form-champ"><label>Date de fondation *</label><input required type="date" value={form.date_creation} onChange={(e) => setField("date_creation", e.target.value)} /></div>
          </div>

          <div className="form-section admin-section">
            <h4>Responsable de référence</h4>
            <p className="sous-titre">Ces informations identifient le responsable administratif. Aucun compte de connexion n'est créé depuis cette interface.</p>
            <div className="form-grid">
              <div className="form-champ"><label>Nom du responsable</label><input value={form.responsable_nom} onChange={(e) => setField("responsable_nom", e.target.value)} /></div>
              <div className="form-champ"><label>Téléphone</label><input inputMode="tel" value={form.responsable_telephone} onChange={(e) => setField("responsable_telephone", e.target.value)} placeholder="+224..." /></div>
              <div className="form-champ"><label>Email</label><input type="email" value={form.responsable_email} onChange={(e) => setField("responsable_email", e.target.value)} /></div>
            </div>
          </div>

          {erreur && <p className="erreur">{erreur}</p>}
          <div className="modal-actions">
            <button className="btn" type="submit">Enregistrer l'église</button>
            <button className="btn btn-secondaire" type="button" onClick={onFerme}>Annuler</button>
          </div>
        </form>
      </div>
    </div>
  );
}
