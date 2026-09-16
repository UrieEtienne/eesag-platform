# EESAG — Bureaux nationaux et bureaux internes

Cette version ajoute une architecture uniforme pour les bureaux métiers :
Femmes, Jeunesse, Enfants, Évangélisation, Hommes, Familles, Communication,
Musique, Missions et autres commissions.

Chaque bureau peut exister au niveau `NATIONAL` (sans église) ou `LOCAL`
(rattaché à une église). La composition est annuelle via `BureauMembreMandat`
et les droits sont délégués via `BureauAdministrateur`.

## API
- `GET/POST /api/bureaux/`
- `GET/POST /api/bureau-membres/`
- `GET/POST /api/bureau-administrateurs/`
- `POST /api/notifications/diffuser/`

## Finance et projets
`Transaction` et `Projet` peuvent désormais appartenir soit à une église,
soit à un bureau. Les deux rattachements ne peuvent pas être utilisés ensemble.

Après installation :

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py check
```
