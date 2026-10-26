import { useMemo, useState } from "react";

const VERSETS = [
  {
    reference: "Jean 3:16",
    texte:
      "Car Dieu a tant aimé le monde qu'il a donné son Fils unique, afin que quiconque croit en lui ne périsse point, mais qu'il ait la vie éternelle.",
  },
  {
    reference: "Psaume 23:1",
    texte:
      "L'Éternel est mon berger : je ne manquerai de rien.",
  },
  {
    reference: "Philippiens 4:13",
    texte:
      "Je puis tout par celui qui me fortifie.",
  },
  {
    reference: "Proverbes 3:5",
    texte:
      "Confie-toi en l'Éternel de tout ton cœur, et ne t'appuie pas sur ta sagesse.",
  },
  {
    reference: "Psaume 119:105",
    texte:
      "Ta parole est une lampe à mes pieds, et une lumière sur mon sentier.",
  },
];

export default function Bible() {
  const [recherche, setRecherche] = useState("");

  const resultats = useMemo(() => {
    const q = recherche.trim().toLowerCase();

    if (!q) {
      return VERSETS;
    }

    return VERSETS.filter(
      (item) =>
        item.reference.toLowerCase().includes(q) ||
        item.texte.toLowerCase().includes(q)
    );
  }, [recherche]);

  return (
    <div className="page-standard">

      <div className="page-hero">
        <div>
          <span className="eyebrow">
            RESSOURCE SPIRITUELLE
          </span>

          <h1>📖 Bible</h1>

          <p>
            Recherchez un passage ou méditez
            sur les Écritures.
          </p>
        </div>
      </div>

      <section className="carte">
        <div className="form-champ">
          <label>Rechercher</label>

          <input
            type="search"
            placeholder="Ex. Jean 3:16, amour, foi..."
            value={recherche}
            onChange={(e) =>
              setRecherche(e.target.value)
            }
          />
        </div>
      </section>

      <div className="dashboard-grid">

        {resultats.map((item) => (
          <article
            key={item.reference}
            className="carte"
          >
            <span className="eyebrow">
              {item.reference}
            </span>

            <p className="bible-verse">
              « {item.texte} »
            </p>
          </article>
        ))}

      </div>

    </div>
  );
}