import { useCallback, useEffect, useState } from "react";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";
import FormulaireMembre from "../components/FormulaireMembre";

function liste(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  return [];
}

export default function Membres() {
  const { utilisateur, estNational, estGestionnaireEglise, estCoordinateur } = useAuth();
  const [membres, setMembres] = useState([]);
  const [q, setQ] = useState("");
  const [show, setShow] = useState(false);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState("");

  // Dans une église locale, seuls l'administrateur local et le pasteur
  // peuvent créer des comptes membres. Le Coordinateur conserve la lecture.
  const peutAjouter = Boolean(
    utilisateur?.eglise &&
    !estNational &&
    estGestionnaireEglise
  );

  const charger = useCallback(async () => {
    setChargement(true);
    setErreur("");
    try {
      const params = { role: "MEMBRE" };
      if (q.trim()) params.search = q.trim();
      const response = await client.get("/utilisateurs/", { params });
      setMembres(liste(response.data));
    } catch (error) {
      setMembres([]);
      setErreur(
        error.response?.data?.detail ||
        "Impossible de charger les membres de cette église."
      );
    } finally {
      setChargement(false);
    }
  }, [q]);

  useEffect(() => {
    const timer = setTimeout(charger, 180);
    return () => clearTimeout(timer);
  }, [charger]);

  return (
    <div>
      <div className="barre-superieure">
        <div>
          <span className="eyebrow">GESTION DE L’ÉGLISE</span>
          <h2>Membres</h2>
          <p className="sous-titre">
            Registre privé de votre église : identité, matricule, département,
            fonction et téléphone.
          </p>
        </div>

        {peutAjouter && (
          <button className="btn" onClick={() => setShow(true)}>
            ＋ Ajouter un membre
          </button>
        )}
      </div>

      <div className="carte" style={{ marginBottom: 16 }}>
        <div className="filtres">
          <input
            placeholder="Rechercher nom, prénom ou matricule…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
        <p className="sous-titre" style={{ marginBottom: 0 }}>
          Église : <b>{utilisateur?.eglise_nom || "votre église"}</b>
        </p>
      </div>

      {erreur && <div className="console-error">{erreur}</div>}

      <div className="carte table-wrap">
        <table>
          <thead>
            <tr>
              <th>Photo</th>
              <th>Matricule</th>
              <th>Nom complet</th>
              <th>Sexe</th>
              <th>Département</th>
              <th>Rôle dans l’église</th>
              <th>Fonction</th>
              <th>Téléphone</th>
            </tr>
          </thead>
          <tbody>
            {membres.map((membre) => (
              <tr key={membre.id}>
                <td>
                  {membre.photo ? (
                    <img className="avatar-photo" src={membre.photo} alt="" />
                  ) : (
                    "—"
                  )}
                </td>
                <td>
                  <span className="code-pill">{membre.identifiant || "—"}</span>
                </td>
                <td>
                  <b>{membre.prenom || ""} {membre.nom || ""}</b>
                </td>
                <td>{membre.sexe || "—"}</td>
                <td>{membre.departement_nom || "—"}</td>
                <td>{membre.role_eglise_nom || "—"}</td>
                <td>{membre.fonction_eglise || "—"}</td>
                <td>{membre.telephone || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {chargement && <div className="empty-state">Chargement des membres…</div>}
        {!chargement && !membres.length && !erreur && (
          <div className="empty-state">Aucun membre enregistré dans cette église.</div>
        )}
      </div>

      {peutAjouter && (
        <p className="sous-titre">
          Les comptes membres sont créés uniquement dans le périmètre de cette
          église et restent rattachés à celle-ci.
        </p>
      )}

      {show && peutAjouter && (
        <FormulaireMembre
          egliseId={utilisateur?.eglise}
          onFerme={() => setShow(false)}
          onCree={() => {
            setShow(false);
            charger();
          }}
        />
      )}
    </div>
  );
}
