import { useEffect, useState } from "react";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Systeme() {
  const { estCoordinateur } = useAuth();
  const [features, setFeatures] = useState([]);
  const [offres, setOffres] = useState([]);
  const [message, setMessage] = useState("");
  const [erreur, setErreur] = useState("");

  const charger = () => client.get("/systeme/fonctionnalites/")
    .then((r) => setFeatures(Array.isArray(r.data) ? r.data : []))
    .catch((e) => setErreur(e.response?.data?.detail || "Impossible de charger les fonctionnalités."));

  useEffect(() => {
    charger();
    client.get("/systeme/offres-mise-a-jour/")
      .then((r) => setOffres(Array.isArray(r.data) ? r.data : []))
      .catch(() => setOffres([]));
  }, []);

  const basculer = async (f) => {
    if (!estCoordinateur && f.verrouillee_globalement && !f.actif) return;
    setMessage("");
    setErreur("");
    try {
      const r = await client.post(`/systeme/fonctionnalites/${f.code}/toggle/`, { actif: !f.actif });
      setMessage(`${f.nom} : ${r.data.actif ? "activée" : "désactivée"} dans le périmètre ${r.data.scope}.`);
      charger();
    } catch (e) {
      setErreur(e.response?.data?.detail || "Modification refusée.");
    }
  };

  return (
    <div className="system-page">
      <div className="page-hero">
        <div>
          <span className="eyebrow">CENTRE DE GESTION</span>
          <h1>Fonctionnalités & mises à jour</h1>
          <p>
            Une fonctionnalité verrouillée par le Coordinateur reste indisponible
            pour tous les autres périmètres jusqu'à sa réactivation par le propriétaire.
          </p>
        </div>
      </div>

      {message && <div className="console-success">{message}</div>}
      {erreur && <div className="console-error">{erreur}</div>}

      <div className="feature-grid">
        {features.map((f) => {
          const globalLock = f.verrouillee_globalement && !f.actif;
          const canToggle = Boolean(f.peut_modifier) && !globalLock;
          return (
            <article className={`carte feature-card ${f.actif ? "enabled" : "disabled"}`} key={f.code}>
              <div>
                <span className="feature-group">{f.groupe}</span>
                <h3>{f.nom}</h3>
                <p>{f.description || "Option de la plateforme."}</p>
                <small>Périmètre : {f.scope}</small>
              </div>
              <div className="feature-foot">
                <span className={`status-chip ${f.actif ? "ok" : "pending"}`}>
                  {globalLock ? "Verrouillée" : f.actif ? "Active" : "Désactivée"}
                </span>
                {globalLock && <small className="feature-lock-text">Seul le Coordinateur peut réactiver cette option.</small>}
                {canToggle && (
                  <button className="btn btn-petit" onClick={() => basculer(f)}>
                    {f.actif ? "Désactiver" : "Activer"}
                  </button>
                )}
              </div>
            </article>
          );
        })}
      </div>

      <div className="carte security-callout">
        <b>Contrôle propriétaire</b>
        <p>
          Une désactivation globale prime sur toute activation locale.
          Les autres utilisateurs ne peuvent pas contourner ce verrouillage.
        </p>
      </div>

      {offres.length > 0 && (
        <section className="carte update-catalog-card">
          <div className="section-header">
            <div>
              <span className="eyebrow">CATALOGUE</span>
              <h3>Mises à jour publiées</h3>
            </div>
          </div>
          <div className="update-catalog-grid">
            {offres.map((o) => (
              <article className="update-offer" key={o.id}>
                <span className="status-chip ok">v{o.version}</span>
                <h4>{o.titre}</h4>
                <p>{o.description}</p>
                <strong>{o.gratuite ? "Gratuite" : `${Number(o.prix || 0).toLocaleString("fr-FR")} ${o.devise}`}</strong>
                <small>La fonctionnalité liée suit les autorisations du propriétaire du système.</small>
              </article>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
