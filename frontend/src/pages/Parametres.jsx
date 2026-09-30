import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

const defaults = {
  accent: "#d6ad3f",
  mode: "light",
  brightness: 100,
  font: 100,
};

export default function Parametres() {
  const [prefs, setPrefs] = useState(() => {
    try {
      const saved = localStorage.getItem("eesag_preferences");

      return {
        ...defaults,
        ...JSON.parse(saved || "{}"),
      };
    } catch {
      return defaults;
    }
  });

  useEffect(() => {
    localStorage.setItem(
      "eesag_preferences",
      JSON.stringify(prefs)
    );

    document.documentElement.style.setProperty(
      "--eesag-accent",
      prefs.accent
    );

    document.documentElement.style.setProperty(
      "--eesag-brightness",
      `${prefs.brightness}%`
    );

    document.documentElement.style.setProperty(
      "--eesag-font-scale",
      `${prefs.font / 100}`
    );

    document.documentElement.dataset.theme = prefs.mode;
  }, [prefs]);

  const set = (key, value) => {
    setPrefs((previous) => ({
      ...previous,
      [key]: value,
    }));
  };

  const accents = [
    ["#d6ad3f", "Or institutionnel"],
    ["#1f8fc4", "Bleu réseau"],
    ["#e85772", "Corail EESAG"],
    ["#20a477", "Vert sécurité"],
  ];

  return (
    <div className="settings-page">
      <div className="page-hero settings-hero">
        <div>
          <span className="eyebrow">
            PROPRIÉTAIRE DU SYSTÈME
          </span>

          <h1>Paramètres EESAG</h1>

          <p>
            Personnalisez l'apparence, la luminosité et les
            réglages du centre de contrôle.
          </p>
        </div>

        <span className="settings-owner-badge">
          COORDINATEUR
        </span>
      </div>

      <div className="settings-grid">
        <section className="carte settings-card">
          <h3>Apparence</h3>

          <label className="settings-label">
            Couleur principale
          </label>

          <div className="accent-options">
            {accents.map(([color, name]) => (
              <button
                key={color}
                type="button"
                className={`accent-choice ${
                  prefs.accent === color ? "selected" : ""
                }`}
                style={{ background: color }}
                onClick={() => set("accent", color)}
                aria-label={name}
                title={name}
              >
                <span>
                  {prefs.accent === color ? "✓" : ""}
                </span>
              </button>
            ))}
          </div>

          <div className="settings-value">
            Mode :{" "}
            <b>
              {prefs.mode === "dark" ? "Sombre" : "Clair"}
            </b>
          </div>

          <div className="segmented">
            <button
              type="button"
              className={
                prefs.mode === "light" ? "selected" : ""
              }
              onClick={() => set("mode", "light")}
            >
              Clair
            </button>

            <button
              type="button"
              className={
                prefs.mode === "dark" ? "selected" : ""
              }
              onClick={() => set("mode", "dark")}
            >
              Sombre
            </button>
          </div>
        </section>

        <section className="carte settings-card">
          <h3>Confort de lecture</h3>

          <label className="settings-label">
            Luminosité : <b>{prefs.brightness}%</b>
          </label>

          <input
            type="range"
            min="75"
            max="120"
            value={prefs.brightness}
            onChange={(e) =>
              set("brightness", Number(e.target.value))
            }
          />

          <label className="settings-label">
            Taille des polices : <b>{prefs.font}%</b>
          </label>

          <input
            type="range"
            min="90"
            max="125"
            value={prefs.font}
            onChange={(e) =>
              set("font", Number(e.target.value))
            }
          />

          <p className="settings-preview">
            Aperçu EESAG — Texte de lecture, tableaux,
            boutons et indicateurs.
          </p>
        </section>

        <section className="carte settings-card">
          <h3>Compte propriétaire</h3>

          <p>
            Votre compte Coordinateur n'est jamais affiché
            dans la liste générale des utilisateurs. Gérez
            vos informations directement.
          </p>

          <Link className="btn" to="/profil">
            Modifier mon compte
          </Link>
        </section>

        <section className="carte settings-card">
          <h3>Réglages opérationnels</h3>

          <div className="settings-list">
            <span>✓ Sécurité des données</span>
            <span>✓ Contrôle national complet</span>
            <span>✓ Journalisation des actions</span>
            <span>✓ Notifications système</span>
          </div>
        </section>
      </div>
    </div>
  );
}
