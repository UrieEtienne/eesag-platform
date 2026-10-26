import { useState } from "react";

export default function Localisation() {
  const [position, setPosition] = useState(null);
  const [erreur, setErreur] = useState("");
  const [recherche, setRecherche] = useState("");
  const [resultat, setResultat] = useState(null);
  const [rechercheEnCours, setRechercheEnCours] =
    useState(false);

  const obtenirPosition = () => {
    setErreur("");

    if (!navigator.geolocation) {
      setErreur(
        "La géolocalisation n'est pas disponible sur cet appareil."
      );
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (data) => {
        setPosition({
          latitude: data.coords.latitude,
          longitude: data.coords.longitude,
          precision: data.coords.accuracy,
        });
      },
      () => {
        setErreur(
          "Impossible d'obtenir votre position. Vérifiez l'autorisation GPS."
        );
      },
      {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 0,
      }
    );
  };

  const rechercherLieu = async (event) => {
    event.preventDefault();

    const nom = recherche.trim();

    if (!nom) return;

    setRechercheEnCours(true);
    setErreur("");
    setResultat(null);

    try {
      const url =
        "https://nominatim.openstreetmap.org/search" +
        `?format=json&limit=5&countrycodes=gn&q=${encodeURIComponent(
          nom
        )}`;

      const response = await fetch(url, {
        headers: {
          Accept: "application/json",
        },
      });

      if (!response.ok) {
        throw new Error();
      }

      const data = await response.json();

      setResultat(data);
    } catch {
      setErreur(
        "La recherche de localisation a échoué."
      );
    } finally {
      setRechercheEnCours(false);
    }
  };

  return (
    <div className="page-standard">

      <div className="page-hero">
        <div>
          <span className="eyebrow">
            GÉOLOCALISATION EESAG
          </span>

          <h1>📍 Localisation</h1>

          <p>
            Localisez-vous ou recherchez
            une église par son nom.
          </p>
        </div>
      </div>

      <section className="dashboard-grid">

        <article className="carte">

          <span className="eyebrow">
            MA POSITION
          </span>

          <h2>GPS en temps réel</h2>

          <p>
            Autorisez votre navigateur à utiliser
            votre position.
          </p>

          <button
            className="btn"
            type="button"
            onClick={obtenirPosition}
          >
            📍 Obtenir ma position
          </button>

          {position && (
            <div className="location-result">
              <p>
                <strong>Latitude :</strong>{" "}
                {position.latitude}
              </p>

              <p>
                <strong>Longitude :</strong>{" "}
                {position.longitude}
              </p>

              <p>
                <strong>Précision :</strong>{" "}
                {Math.round(position.precision)} m
              </p>

              <a
                className="btn"
                target="_blank"
                rel="noopener noreferrer"
                href={`https://www.google.com/maps?q=${position.latitude},${position.longitude}`}
              >
                Ouvrir dans Maps
              </a>
            </div>
          )}

        </article>

        <article className="carte">

          <span className="eyebrow">
            RECHERCHE INTELLIGENTE
          </span>

          <h2>Rechercher une église</h2>

          <form
            onSubmit={rechercherLieu}
            className="form-section"
          >
            <div className="form-champ">
              <label>
                Nom de l'église ou localité
              </label>

              <input
                value={recherche}
                onChange={(e) =>
                  setRecherche(e.target.value)
                }
                placeholder="Ex. Église EESAG Conakry"
              />
            </div>

            <button
              className="btn btn-primary"
              disabled={rechercheEnCours}
            >
              {rechercheEnCours
                ? "Recherche…"
                : "Rechercher"}
            </button>
          </form>

          {resultat?.length > 0 && (
            <div className="location-results">
              {resultat.map((item) => (
                <div
                  className="location-result"
                  key={item.place_id}
                >
                  <strong>
                    {item.display_name}
                  </strong>

                  <small>
                    Latitude : {item.lat}
                    <br />
                    Longitude : {item.lon}
                  </small>

                  <a
                    className="btn"
                    target="_blank"
                    rel="noopener noreferrer"
                    href={`https://www.google.com/maps?q=${item.lat},${item.lon}`}
                  >
                    Voir sur la carte
                  </a>
                </div>
              ))}
            </div>
          )}

        </article>
      </section>

      {erreur && (
        <div className="carte status-error">
          {erreur}
        </div>
      )}

    </div>
  );
}