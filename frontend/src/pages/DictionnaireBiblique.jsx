import { useMemo, useState } from "react";

const TERMES = [
  {
    terme: "Alliance",
    definition:
      "Engagement établi entre Dieu et son peuple, exprimant une relation fondée sur les promesses de Dieu.",
  },
  {
    terme: "Grâce",
    definition:
      "Faveur imméritée accordée par Dieu.",
  },
  {
    terme: "Foi",
    definition:
      "Confiance en Dieu et en ses promesses.",
  },
  {
    terme: "Évangile",
    definition:
      "Bonne nouvelle du salut en Jésus-Christ.",
  },
  {
    terme: "Disciple",
    definition:
      "Personne qui suit l'enseignement et l'exemple de Jésus-Christ.",
  },
  {
    terme: "Prière",
    definition:
      "Communication avec Dieu dans laquelle le croyant peut louer, remercier, demander et confesser.",
  },
];

export default function DictionnaireBiblique() {
  const [recherche, setRecherche] = useState("");

  const resultats = useMemo(() => {
    const q = recherche.toLowerCase().trim();

    if (!q) return TERMES;

    return TERMES.filter(
      (item) =>
        item.terme.toLowerCase().includes(q) ||
        item.definition.toLowerCase().includes(q)
    );
  }, [recherche]);

  return (
    <div className="page-standard">

      <div className="page-hero">
        <div>
          <span className="eyebrow">
            ÉTUDE BIBLIQUE
          </span>

          <h1>📚 Dictionnaire biblique</h1>

          <p>
            Recherchez un terme, une notion ou
            une expression biblique.
          </p>
        </div>
      </div>

      <section className="carte">
        <div className="form-champ">
          <label>Rechercher un terme</label>

          <input
            type="search"
            value={recherche}
            onChange={(e) =>
              setRecherche(e.target.value)
            }
            placeholder="Ex. grâce, foi, alliance..."
          />
        </div>
      </section>

      <div className="dashboard-grid">
        {resultats.map((item) => (
          <article
            key={item.terme}
            className="carte"
          >
            <span className="eyebrow">
              TERME BIBLIQUE
            </span>

            <h2>{item.terme}</h2>

            <p>{item.definition}</p>
          </article>
        ))}
      </div>

    </div>
  );
}