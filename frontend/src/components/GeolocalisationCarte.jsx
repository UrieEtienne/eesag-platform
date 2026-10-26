import { useState } from "react";
import L from "leaflet";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  useMap,
  useMapEvents,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import client from "../api/client";

// Chemins des icônes Leaflet pris en charge par Vite.
const iconeRetina = new URL(
  "leaflet/dist/images/marker-icon-2x.png",
  import.meta.url
).href;
const iconeMarqueur = new URL(
  "leaflet/dist/images/marker-icon.png",
  import.meta.url
).href;
const ombreMarqueur = new URL(
  "leaflet/dist/images/marker-shadow.png",
  import.meta.url
).href;

const icone = L.icon({
  iconRetinaUrl: iconeRetina,
  iconUrl: iconeMarqueur,
  shadowUrl: ombreMarqueur,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

L.Marker.prototype.options.icon = icone;

const CENTRE_GUINEE = [9.537, -13.678];

function AjusterCarte({ point }) {
  const map = useMap();

  if (point) {
    map.flyTo([point.latitude, point.longitude], 14, {
      duration: 0.8,
    });
  }

  return null;
}

function SelectionSurCarte({ onSelection }) {
  useMapEvents({
    click(e) {
      onSelection({
        latitude: e.latlng.lat,
        longitude: e.latlng.lng,
      });
    },
  });

  return null;
}

export default function GeolocalisationCarte() {
  const [recherche, setRecherche] = useState("");
  const [resultats, setResultats] = useState([]);
  const [depart, setDepart] = useState(null);
  const [arrivee, setArrivee] = useState(null);
  const [lieuSelectionne, setLieuSelectionne] = useState(null);
  const [itineraire, setItineraire] = useState(null);
  const [chargement, setChargement] = useState(false);
  const [erreur, setErreur] = useState("");
  const [message, setMessage] = useState("");

  const rechercherLieu = async (e) => {
    e.preventDefault();
    setErreur("");
    setMessage("");
    setResultats([]);
    setItineraire(null);

    if (!recherche.trim()) {
      setErreur("Saisis le nom d'une église ou d'une localité.");
      return;
    }

    setChargement(true);

    try {
      const { data } = await client.post("/geo/recherche-eglise/", {
        nom: recherche.trim(),
      });

      setResultats(data.resultats || []);

      if (!data.resultats?.length) {
        setMessage("Aucun résultat trouvé.");
      }
    } catch (error) {
      setErreur(
        error.response?.data?.detail ||
          "Impossible de rechercher ce lieu. Vérifie la connexion puis réessaie."
      );
    } finally {
      setChargement(false);
    }
  };

  const utiliserGPS = () => {
    setErreur("");
    setMessage("");
    setItineraire(null);

    if (!navigator.geolocation) {
      setErreur("La géolocalisation n'est pas prise en charge par ce navigateur.");
      return;
    }

    setChargement(true);

    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        const point = {
          latitude: coords.latitude,
          longitude: coords.longitude,
        };

        setDepart(point);
        setLieuSelectionne(point);
        setMessage("Votre position actuelle a été récupérée.");
        setChargement(false);
      },
      (error) => {
        const messages = {
          1: "Autorisation GPS refusée. Autorise la localisation dans ton navigateur.",
          2: "Position GPS indisponible. Réessaie dans quelques instants.",
          3: "La recherche GPS a expiré. Réessaie.",
        };

        setErreur(messages[error.code] || "Impossible de récupérer votre position.");
        setChargement(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 30000,
      }
    );
  };

  const choisirDestination = (point) => {
    setArrivee({
      latitude: Number(point.latitude),
      longitude: Number(point.longitude),
    });
    setLieuSelectionne({
      latitude: Number(point.latitude),
      longitude: Number(point.longitude),
    });
    setItineraire(null);
    setMessage("Destination sélectionnée. Tu peux calculer l'itinéraire.");
    setErreur("");
  };

  const calculerItineraire = async () => {
    setErreur("");
    setMessage("");
    setItineraire(null);

    if (!depart || !arrivee) {
      setErreur(
        "Définis un départ avec le GPS et une destination avec la recherche ou la carte."
      );
      return;
    }

    setChargement(true);

    try {
      const { data } = await client.post("/geo/itineraire/", {
        depart,
        arrivee,
      });

      setItineraire(data);
      setLieuSelectionne(arrivee);
      setMessage("Itinéraire calculé.");
    } catch (error) {
      setErreur(
        error.response?.data?.detail ||
          "Impossible de calculer l'itinéraire pour le moment."
      );
    } finally {
      setChargement(false);
    }
  };

  const choisirSurCarte = (point) => {
    setArrivee(point);
    setLieuSelectionne(point);
    setItineraire(null);
    setMessage("Destination définie sur la carte.");
    setErreur("");
  };

  const ligne = itineraire?.geometry?.coordinates?.map(
    ([longitude, latitude]) => [latitude, longitude]
  );

  const positionDepart = depart
    ? [depart.latitude, depart.longitude]
    : null;

  const positionArrivee = arrivee
    ? [arrivee.latitude, arrivee.longitude]
    : null;

  const positionCentrale = lieuSelectionne
    ? [lieuSelectionne.latitude, lieuSelectionne.longitude]
    : CENTRE_GUINEE;

  return (
    <section className="carte" style={{ marginBottom: 24 }}>
      <h3>Géolocalisation des églises et itinéraires</h3>

      <form
        onSubmit={rechercherLieu}
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 8,
          marginBottom: 12,
        }}
      >
        <input
          value={recherche}
          onChange={(e) => setRecherche(e.target.value)}
          placeholder="Nom d'une église, ville ou localité en Guinée"
          aria-label="Lieu à rechercher"
          maxLength={200}
          style={{ flex: "1 1 260px", minWidth: 0 }}
        />
        <button className="btn" type="submit" disabled={chargement}>
          Rechercher
        </button>
        <button
          className="btn"
          type="button"
          onClick={utiliserGPS}
          disabled={chargement}
        >
          Utiliser ma position GPS
        </button>
      </form>

      <p style={{ fontSize: 13, color: "#64748b" }}>
        Astuce : clique sur la carte pour définir la destination. Le GPS nécessite
        ton autorisation et une connexion sécurisée en production (HTTPS).
      </p>

      {erreur && (
        <div role="alert" style={{ color: "#b91c1c", margin: "10px 0" }}>
          {erreur}
        </div>
      )}

      {message && (
        <div role="status" style={{ color: "#166534", margin: "10px 0" }}>
          {message}
        </div>
      )}

      {resultats.length > 0 && (
        <div style={{ margin: "12px 0" }}>
          <strong>Résultats de recherche</strong>
          <ul style={{ paddingLeft: 20 }}>
            {resultats.map((lieu, index) => (
              <li key={`${lieu.osm_type}-${lieu.osm_id}-${index}`} style={{ margin: "8px 0" }}>
                <div>{lieu.nom}</div>
                <small>{lieu.adresse}</small>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 5 }}>
                  <button
                    type="button"
                    className="btn btn-petit"
                    onClick={() => {
                      setLieuSelectionne({
                        latitude: lieu.latitude,
                        longitude: lieu.longitude,
                      });
                      setMessage("Lieu affiché sur la carte.");
                      setErreur("");
                    }}
                  >
                    Voir sur la carte
                  </button>
                  <button
                    type="button"
                    className="btn btn-petit"
                    onClick={() => choisirDestination(lieu)}
                  >
                    Choisir comme destination
                  </button>
                </div>
              </li>
            ))}
          </ul>
          <small>Résultats fournis par OpenStreetMap / Nominatim.</small>
        </div>
      )}

      <div
        style={{
          width: "100%",
          height: 460,
          borderRadius: 10,
          overflow: "hidden",
          border: "1px solid #cbd5e1",
        }}
      >
        <MapContainer
          center={CENTRE_GUINEE}
          zoom={7}
          scrollWheelZoom
          style={{ height: "100%", width: "100%" }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <SelectionSurCarte onSelection={choisirSurCarte} />
          <AjusterCarte point={lieuSelectionne} />

          {positionDepart && (
            <Marker position={positionDepart}>
              <Popup>Point de départ : votre position GPS</Popup>
            </Marker>
          )}

          {positionArrivee && (
            <Marker position={positionArrivee}>
              <Popup>Destination sélectionnée</Popup>
            </Marker>
          )}

          {ligne?.length > 0 && (
            <Polyline positions={ligne} pathOptions={{ color: "#2563eb", weight: 5 }} />
          )}
        </MapContainer>
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginTop: 12 }}>
        <button
          className="btn"
          type="button"
          onClick={calculerItineraire}
          disabled={chargement}
        >
          Calculer l'itinéraire
        </button>
        <button
          className="btn"
          type="button"
          onClick={() => {
            setDepart(null);
            setArrivee(null);
            setLieuSelectionne(null);
            setItineraire(null);
            setErreur("");
            setMessage("");
          }}
        >
          Réinitialiser les points
        </button>
      </div>

      {itineraire && (
        <div style={{ marginTop: 14 }}>
          <strong>Itinéraire routier</strong>
          <p>
            Distance : <strong>{itineraire.distance_km} km</strong>
          </p>
          <p>
            Durée estimée : <strong>{itineraire.duree_minutes} minutes</strong>
          </p>
          <small>
            Calcul fourni par OSRM. La durée est indicative et peut varier selon
            les conditions réelles de circulation.
          </small>
        </div>
      )}
    </section>
  );
}
