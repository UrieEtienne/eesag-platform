import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const VERSETS = [
  {
    texte:
      "Je puis tout par celui qui me fortifie.",
    reference: "Philippiens 4:13",
  },
  {
    texte:
      "L'Éternel est mon berger : je ne manquerai de rien.",
    reference: "Psaume 23:1",
  },
  {
    texte:
      "Confie-toi en l'Éternel de tout ton cœur.",
    reference: "Proverbes 3:5",
  },
  {
    texte:
      "Que tout ce que vous faites se fasse avec amour.",
    reference: "1 Corinthiens 16:14",
  },
  {
    texte:
      "Je vous laisse la paix, je vous donne ma paix.",
    reference: "Jean 14:27",
  },
];

const IMAGES = [
  "/assets/accueil/eglise-1.jpg",
  "/assets/accueil/eglise-2.jpg",
  "/assets/accueil/eglise-3.jpg",
  "/assets/accueil/bible-1.jpg",
];

export default function EspaceAccueil() {
  const {
    utilisateur,
    chargement,
    estMembre,
  } = useAuth();

  const [imageIndex, setImageIndex] = useState(0);

  // Défilement automatique du carrousel toutes les 5 secondes.
  useEffect(() => {
    const timer = window.setInterval(() => {
      setImageIndex((current) => (current + 1) % IMAGES.length);
    }, 5000);

    return () => window.clearInterval(timer);
  }, []);

  const verset = useMemo(() => {
    const index =
      new Date().getDate() % VERSETS.length;

    return VERSETS[index];
  }, []);

  if (chargement) {
    return (
      <div className="page-loading">
        <div className="loading-spinner" />
        <span>Chargement EESAG…</span>
      </div>
    );
  }

  const nomEglise =
    utilisateur?.eglise_nom ||
    utilisateur?.eglise?.nom ||
    "Votre église";

  return (
    <div className="eesag-home">

      {/* HERO */}

      <section
        className="home-hero"
        style={{
          backgroundImage: `linear-gradient(
            rgba(5, 10, 18, .65),
            rgba(5, 10, 18, .78)
          ), url("${IMAGES[imageIndex]}")`,
        }}
      >
        <div className="home-hero-content">

          <span className="eyebrow">
            EESAG · ESPACE PERSONNEL
          </span>

          <h1>
            Bienvenue{" "}
            {utilisateur?.prenom || ""}
          </h1>

          <p className="home-church-name">
            {nomEglise}
          </p>

          <p>
            Votre espace spirituel, communautaire
            et informatif au sein de la plateforme
            EESAG.
          </p>

          <div className="home-actions">
            <Link
              to="/bible"
              className="btn btn-primary"
            >
              📖 Ouvrir la Bible
            </Link>

            <Link
              to="/localisation"
              className="btn"
            >
              📍 Localiser
            </Link>
          </div>
        </div>

        <div className="home-slider-controls">
          {IMAGES.map((_, index) => (
            <button
              key={index}
              type="button"
              onClick={() => setImageIndex(index)}
              className={
                index === imageIndex
                  ? "active"
                  : ""
              }
              aria-label={`Image ${index + 1}`}
            />
          ))}
        </div>
      </section>

      {/* VERSET */}

      <section className="daily-verse-card carte">
        <span className="eyebrow">
          VERSET DU JOUR
        </span>

        <blockquote>
          « {verset.texte} »
        </blockquote>

        <strong>
          — {verset.reference}
        </strong>
      </section>

      {/* SERVICES */}

      <section className="home-section">

        <div className="section-heading">
          <div>
            <span className="eyebrow">
              SERVICES EESAG
            </span>

            <h2>
              Tout votre espace au même endroit
            </h2>
          </div>
        </div>

        <div className="home-service-grid">

          <Link to="/bureau-national" className="home-service-card">
            <span>◆</span>
            <h3>Bureau national</h3>
            <p>
              Informations, responsables,
              activités et communications
              du Bureau national.
            </p>
          </Link>

          <Link to="/bible" className="home-service-card">
            <span>📖</span>
            <h3>Bible</h3>
            <p>
              Consultez les textes bibliques
              et retrouvez rapidement un passage.
            </p>
          </Link>

          <Link
            to="/dictionnaire-biblique"
            className="home-service-card"
          >
            <span>📚</span>
            <h3>Dictionnaire biblique</h3>
            <p>
              Recherchez la signification
              des termes et personnages bibliques.
            </p>
          </Link>

          <Link
            to="/localisation"
            className="home-service-card"
          >
            <span>📍</span>
            <h3>Localisation</h3>
            <p>
              Utilisez votre GPS ou recherchez
              une église par son nom.
            </p>
          </Link>

          <Link
            to="/notifications"
            className="home-service-card"
          >
            <span>🔔</span>
            <h3>Communications</h3>
            <p>
              Actualités, annonces et
              communications importantes.
            </p>
          </Link>

          <Link
            to="/partager"
            className="home-service-card"
          >
            <span>↗</span>
            <h3>Partager EESAG</h3>
            <p>
              Invitez d'autres personnes
              à découvrir la plateforme.
            </p>
          </Link>

          <Link
            to="/dons"
            className="home-service-card donation-card"
          >
            <span>❤</span>
            <h3>Faire un don</h3>
            <p>
              Soutenez l'œuvre par
              Orange Money ou MTN Mobile Money.
            </p>
          </Link>

          <Link
            to="/a-propos"
            className="home-service-card"
          >
            <span>ⓘ</span>
            <h3>À propos</h3>
            <p>
              Découvrez EESAG, son objectif
              et son développeur.
            </p>
          </Link>
        </div>
      </section>

      {/* ÉGLISE */}

      <section className="home-church-panel carte">

        <div>
          <h2>{nomEglise}</h2>

          <p>
            Retrouvez les informations liées
            à votre communauté et utilisez
            les services disponibles.
          </p>
        </div>

        <Link
          to="/profil"
          className="btn"
        >
          Mon profil
        </Link>
      </section>

      {/* OBJECTIF */}

      <section className="home-purpose carte">

        <span className="eyebrow">
          NOTRE OBJECTIF
        </span>

        <h2>
          Une plateforme au service de
          l'Église et de ses membres
        </h2>

        <p>
          EESAG vise à rapprocher les membres,
          les églises et les structures nationales
          grâce à une plateforme moderne,
          sécurisée et accessible.
        </p>

      </section>
    </div>
  );
}