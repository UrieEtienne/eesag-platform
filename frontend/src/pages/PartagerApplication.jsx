export default function PartagerApplication() {
  const url = window.location.origin;

  const partager = async () => {
    const data = {
      title: "EESAG",
      text:
        "Découvrez la plateforme EESAG.",
      url,
    };

    if (navigator.share) {
      try {
        await navigator.share(data);
      } catch {
        // L'utilisateur a annulé.
      }

      return;
    }

    try {
      await navigator.clipboard.writeText(url);

      alert(
        "Lien EESAG copié dans le presse-papiers."
      );
    } catch {
      alert(
        `Copiez ce lien pour partager EESAG : ${url}`
      );
    }
  };

  return (
    <div className="page-standard">

      <div className="page-hero">
        <div>
          <span className="eyebrow">
            COMMUNAUTÉ
          </span>

          <h1>↗ Partager EESAG</h1>

          <p>
            Invitez vos proches à découvrir
            la plateforme.
          </p>
        </div>
      </div>

      <section className="carte share-card">

        <div className="share-icon">
          ↗
        </div>

        <h2>
          Partager l'application
        </h2>

        <p>
          Envoyez EESAG à un membre,
          une famille, une église ou
          une personne intéressée.
        </p>

        <button
          className="btn btn-primary"
          type="button"
          onClick={partager}
        >
          Partager maintenant
        </button>

      </section>

    </div>
  );
}
