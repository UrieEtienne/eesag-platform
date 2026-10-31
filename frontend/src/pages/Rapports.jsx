
import { useState } from "react";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";

const PERIODES = [
  ["semaine", "Cette semaine"],
  ["mois", "Ce mois"],
  ["annee", "Cette année"],
  ["personnalisee", "Personnalisée"],
];

const formatNombre = (valeur) =>
  Number(valeur || 0).toLocaleString("fr-FR");

export default function Rapports() {
  const { utilisateur } = useAuth();

  const [form, setForm] = useState({
    periode: "annee",
    debut: "",
    fin: "",
    membres: true,
    finances: true,
    projets: true,
  });

  const [preview, setPreview] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const modifier = (champ, valeur) => {
    setForm((ancien) => ({ ...ancien, [champ]: valeur }));
  };

  const params = () => {
    const p = new URLSearchParams({
      periode: form.periode,
      membres: form.membres ? "1" : "0",
      finances: form.finances ? "1" : "0",
      projets: form.projets ? "1" : "0",
    });

    if (form.debut) p.set("debut", form.debut);
    if (form.fin) p.set("fin", form.fin);

    return p;
  };

  const apercu = async () => {
    setErr("");

    if (
      form.periode === "personnalisee" &&
      (!form.debut || !form.fin)
    ) {
      setErr("Veuillez renseigner les deux dates de la période.");
      return;
    }

    if (
      form.periode === "personnalisee" &&
      form.debut > form.fin
    ) {
      setErr("La date de début doit précéder la date de fin.");
      return;
    }

    if (!form.membres && !form.finances && !form.projets) {
      setErr("Sélectionnez au moins une rubrique pour le rapport.");
      return;
    }

    setBusy(true);
    setPreview(null);

    try {
      const response = await client.get(
        `/stats/rapport-apercu/?${params()}`
      );
      setPreview(response.data);
    } catch (error) {
      setErr(
        error.response?.data?.detail || "Impossible de générer l’aperçu."
      );
    } finally {
      setBusy(false);
    }
  };

  const exporter = async () => {
    if (!preview) return;

    setBusy(true);
    setErr("");

    try {
      let path = "/stats/rapport-national/";

      if (preview.scope?.type === "EGLISE") {
        path = `/stats/rapport/${preview.scope.eglise_id}/`;
      }

      if (preview.scope?.type === "BUREAU") {
        path = `/stats/rapport-bureau/${preview.scope.bureau_id}/`;
      }

      const response = await client.get(`${path}?${params()}`, {
        responseType: "blob",
      });

      const url = URL.createObjectURL(response.data);
      const lien = document.createElement("a");

      lien.href = url;
      lien.download = `rapport-${String(
        preview.label || "eesag"
      ).replace(/\s+/g, "-")}.pdf`;

      document.body.appendChild(lien);
      lien.click();
      lien.remove();

      URL.revokeObjectURL(url);
    } catch (error) {
      setErr(
        error.response?.data?.detail || "Impossible d’exporter le rapport."
      );
    } finally {
      setBusy(false);
    }
  };

  const nomStructure =
    preview?.label || utilisateur?.eglise_nom || "Mon périmètre";

  return (
    <div className="reports-page page-rapports">
      <header className="page-hero reports-hero rapports-hero">
        <div className="rapports-hero-content">
          <span className="eyebrow">ESPACE DE GESTION · EESAG</span>
          <h1>Rapports et statistiques</h1>
          <p>
            Préparez, consultez et exportez les rapports de votre structure.
            Vérifiez les données avant de générer le document PDF.
          </p>
        </div>

        <div className="rapports-hero-info">
          <span className="rapports-hero-icon">▤</span>
          <small>PÉRIMÈTRE DU RAPPORT</small>
          <strong>{nomStructure}</strong>
          <span className="rapports-lock">✓ Périmètre sécurisé</span>
        </div>
      </header>

      {err && (
        <div className="console-error rapports-error" role="alert">
          <span>⚠</span>
          {err}
        </div>
      )}

      <section className="rapports-builder carte">
        <div className="rapports-section-heading">
          <div>
            <span className="eyebrow">CONFIGURATION</span>
            <h2>Personnaliser le rapport</h2>
            <p>Choisissez la période et les informations à inclure.</p>
          </div>
          <span className="scope-badge">Périmètre verrouillé</span>
        </div>

        <div className="rapports-field-group">
          <label className="rapports-label">1. Période du rapport</label>

          <div className="report-periods rapports-periods">
            {PERIODES.map(([valeur, libelle]) => (
              <button
                type="button"
                key={valeur}
                className={form.periode === valeur ? "selected" : ""}
                aria-pressed={form.periode === valeur}
                onClick={() => modifier("periode", valeur)}
              >
                {libelle}
              </button>
            ))}
          </div>
        </div>

        {form.periode === "personnalisee" && (
          <div className="rapports-dates">
            <div className="form-champ">
              <label htmlFor="rapport-debut">Date de début</label>
              <input
                id="rapport-debut"
                type="date"
                value={form.debut}
                onChange={(event) => modifier("debut", event.target.value)}
              />
            </div>

            <div className="form-champ">
              <label htmlFor="rapport-fin">Date de fin</label>
              <input
                id="rapport-fin"
                type="date"
                min={form.debut || undefined}
                value={form.fin}
                onChange={(event) => modifier("fin", event.target.value)}
              />
            </div>
          </div>
        )}

        <div className="rapports-divider" />

        <div className="rapports-field-group">
          <label className="rapports-label">2. Rubriques à inclure</label>

          <div className="report-checks rapports-checks">
            <label className={form.membres ? "active" : ""}>
              <input
                type="checkbox"
                checked={form.membres}
                onChange={(event) =>
                  modifier("membres", event.target.checked)
                }
              />
              <span className="rapports-check-icon">♙</span>
              <span>
                <strong>Membres et démographie</strong>
                <small>Effectifs et répartition par sexe</small>
              </span>
            </label>

            <label className={form.finances ? "active" : ""}>
              <input
                type="checkbox"
                checked={form.finances}
                onChange={(event) =>
                  modifier("finances", event.target.checked)
                }
              />
              <span className="rapports-check-icon">₣</span>
              <span>
                <strong>Comptabilité</strong>
                <small>Entrées, sorties et solde</small>
              </span>
            </label>

            <label className={form.projets ? "active" : ""}>
              <input
                type="checkbox"
                checked={form.projets}
                onChange={(event) =>
                  modifier("projets", event.target.checked)
                }
              />
              <span className="rapports-check-icon">▦</span>
              <span>
                <strong>Projets et budgets</strong>
                <small>Nombre de projets et budget prévu</small>
              </span>
            </label>
          </div>
        </div>

        <div className="rapports-actions">
          <button
            type="button"
            className="btn rapports-btn-primary"
            onClick={apercu}
            disabled={busy}
          >
            {busy ? "Préparation en cours…" : "⌕ Générer l’aperçu"}
          </button>

          <button
            type="button"
            className="btn btn-secondaire"
            onClick={() => window.print()}
            disabled={busy}
          >
            Imprimer la page
          </button>
        </div>
      </section>

      {preview && (
        <section className="rapports-preview carte">
          <div className="rapports-section-heading rapports-preview-heading">
            <div>
              <span className="eyebrow">RÉSULTAT DE LA PRÉVISUALISATION</span>
              <h2>{preview.label}</h2>
              <p>
                Période : {preview.periode?.debut || "—"} au{" "}
                {preview.periode?.fin || "—"}
              </p>
            </div>

            <span className="rapports-preview-status">
              <span /> Aperçu disponible
            </span>
          </div>

          <div className="report-preview-grid rapports-preview-grid">
            {preview.membres && (
              <article className="rapports-metric">
                <span className="rapports-metric-icon">♙</span>
                <small>Membres actifs</small>
                <strong>{formatNombre(preview.membres.total)}</strong>
                <p>
                  {formatNombre(preview.membres.hommes)} hommes ·{" "}
                  {formatNombre(preview.membres.femmes)} femmes
                </p>
              </article>
            )}

            {preview.finances && (
              <article className="rapports-metric">
                <span className="rapports-metric-icon">₣</span>
                <small>Solde financier</small>
                <strong>{formatNombre(preview.finances.solde)} GNF</strong>
                <p>
                  {formatNombre(preview.finances.entrees)} entrées ·{" "}
                  {formatNombre(preview.finances.sorties)} sorties
                </p>
              </article>
            )}

            {preview.projets && (
              <article className="rapports-metric">
                <span className="rapports-metric-icon">▦</span>
                <small>Projets</small>
                <strong>{formatNombre(preview.projets.nombre)}</strong>
                <p>
                  Budget prévu :{" "}
                  {formatNombre(preview.projets.budget_prevu)} GNF
                </p>
              </article>
            )}
          </div>

          <div className="rapports-confirmation">
            <span>✓</span>
            <p>
              Vérifiez les données avant l’export. Le rapport PDF sera généré
              uniquement pour <strong>{preview.label}</strong>.
            </p>
          </div>

          <div className="rapports-export-actions">
            <button
              type="button"
              className="btn rapports-btn-primary"
              onClick={exporter}
              disabled={busy}
            >
              {busy ? "Exportation en cours…" : "↓ Télécharger le rapport PDF"}
            </button>
          </div>
        </section>
      )}
    </div>
  );
}
