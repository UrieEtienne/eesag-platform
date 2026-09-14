import { useEffect, useState } from "react";
import client from "../api/client";

export default function RechercheMembre() {
  const [terme, setTerme] = useState("");
  const [resultats, setResultats] = useState([]);

  useEffect(() => {
    if (terme.trim().length < 2) { setResultats([]); return; }
    const delai = setTimeout(() => {
      client.get("/membres/recherche/", { params: { q: terme } }).then((res) => setResultats(res.data));
    }, 300);
    return () => clearTimeout(delai);
  }, [terme]);

  return (
    <div>
      <div className="barre-superieure"><h2>Rechercher un membre</h2></div>
      <div className="carte">
        <input
          style={{ width: "100%", padding: 10, fontSize: 16 }}
          placeholder="Tapez un identifiant, un nom ou un prénom..."
          value={terme}
          onChange={(e) => setTerme(e.target.value)}
        />
      </div>
      {resultats.length > 0 && (
        <div className="carte">
          <table>
            <thead><tr><th>Identifiant</th><th>Nom</th><th>Église</th><th>Rôle</th></tr></thead>
            <tbody>
              {resultats.map((m) => (
                <tr key={m.id}>
                  <td>{m.identifiant}</td><td>{m.nom_complet}</td>
                  <td>{m.eglise_nom || "—"}</td><td>{m.role_libelle}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
