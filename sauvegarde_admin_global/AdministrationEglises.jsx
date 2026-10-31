import { useState } from "react";
import FormulaireEglise from "../components/FormulaireEglise";

export default function AdministrationEglises() {
  const [message, setMessage] = useState("");

  const handleCree = (resultat) => {
    setMessage(
      resultat?.nom
        ? `L'église « ${resultat.nom} » a été créée avec succès.`
        : "L'église a été créée avec succès."
    );
  };

  return (
    <div className="page">

      {/* =====================================================
          EN-TÊTE
      ====================================================== */}

      <div className="page-hero">
        <div>
          <span className="eyebrow">
            ADMINISTRATION NATIONALE
          </span>

          <h1>Créer une église</h1>

          <p>
            Enregistrez une nouvelle église dans EESAG,
            puis créez son espace privé et son
            administrateur local.
          </p>
        </div>
      </div>

      {/* =====================================================
          MESSAGE
      ====================================================== */}

      {message && (
        <div className="console-success">
          {message}
        </div>
      )}

      {/* =====================================================
          FORMULAIRE
      ====================================================== */}

      <FormulaireEglise
        onFerme={() => {
          setMessage("");
        }}
        onCree={handleCree}
      />

    </div>
  );
}