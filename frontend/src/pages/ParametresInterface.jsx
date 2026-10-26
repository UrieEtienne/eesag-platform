import { useEffect, useState } from "react";

export default function ParametresInterface() {
  const [taille, setTaille] = useState(
    localStorage.getItem("eesag_font_size") || "normal"
  );

  const [theme, setTheme] = useState(
    localStorage.getItem("eesag_theme") || "system"
  );

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("eesag_theme", theme);
  }, [theme]);

  useEffect(() => {
    document.documentElement.dataset.fontSize = taille;
    localStorage.setItem("eesag_font_size", taille);
  }, [taille]);

  return (
    <div className="page-standard">

      <div className="page-hero">
        <div>
          <span className="eyebrow">
            PERSONNALISATION
          </span>

          <h1>⚙ Paramètres</h1>

          <p>
            Personnalisez votre expérience EESAG.
          </p>
        </div>
      </div>

      <section className="dashboard-grid">

        <div className="carte">

          <h2>Mode d'affichage</h2>

          <div className="form-champ">
            <label>Thème</label>

            <select
              value={theme}
              onChange={(e) =>
                setTheme(e.target.value)
              }
            >
              <option value="system">
                Automatique
              </option>

              <option value="light">
                Clair
              </option>

              <option value="dark">
                Sombre
              </option>
            </select>
          </div>

        </div>

        <div className="carte">

          <h2>Taille du texte</h2>

          <div className="form-champ">
            <label>Taille</label>

            <select
              value={taille}
              onChange={(e) =>
                setTaille(e.target.value)
              }
            >
              <option value="small">
                Petite
              </option>

              <option value="normal">
                Normale
              </option>

              <option value="large">
                Grande
              </option>

              <option value="xlarge">
                Très grande
              </option>
            </select>
          </div>

        </div>

      </section>

    </div>
  );
}