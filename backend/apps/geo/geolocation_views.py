import os
import requests

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"

USER_AGENT = os.getenv(
    "NOMINATIM_USER_AGENT",
    "EESAG/1.0 (contact: configure-an-admin-email)"
)


def coordonnee_valide(valeur, minimum, maximum):
    try:
        valeur = float(valeur)
    except (TypeError, ValueError):
        return None

    if not minimum <= valeur <= maximum:
        return None

    return valeur


class RechercheEgliseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        nom = str(request.data.get("nom", "")).strip()

        if not nom:
            return Response(
                {"detail": "Le nom du lieu est obligatoire."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(nom) > 200:
            return Response(
                {"detail": "Le nom ne doit pas dépasser 200 caractères."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            response = requests.get(
                NOMINATIM_URL,
                params={
                    "q": f"{nom}, Guinée",
                    "format": "jsonv2",
                    "addressdetails": 1,
                    "limit": 5,
                    "countrycodes": "gn",
                },
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept-Language": "fr",
                },
                timeout=12,
            )
            response.raise_for_status()
            resultats = response.json()

        except (requests.RequestException, ValueError):
            return Response(
                {
                    "detail": (
                        "Le service de géocodage est momentanément "
                        "indisponible. Réessaie plus tard."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        candidats = []

        for lieu in resultats:
            try:
                latitude = float(lieu["lat"])
                longitude = float(lieu["lon"])
            except (KeyError, TypeError, ValueError):
                continue

            adresse = lieu.get("address", {})

            candidats.append({
                "nom": lieu.get("name") or nom,
                "adresse": lieu.get("display_name", ""),
                "latitude": latitude,
                "longitude": longitude,
                "region": (
                    adresse.get("state")
                    or adresse.get("region")
                    or ""
                ),
                "prefecture": (
                    adresse.get("county")
                    or adresse.get("city")
                    or adresse.get("municipality")
                    or ""
                ),
                "localite": (
                    adresse.get("suburb")
                    or adresse.get("village")
                    or adresse.get("town")
                    or adresse.get("city")
                    or ""
                ),
                "source": "OpenStreetMap / Nominatim",
                "osm_type": lieu.get("osm_type"),
                "osm_id": lieu.get("osm_id"),
            })

        if not candidats:
            return Response(
                {
                    "detail": (
                        "Aucun lieu correspondant trouvé. "
                        "Essaie avec un nom plus précis ou une adresse."
                    ),
                    "resultats": [],
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({
            "recherche": nom,
            "nombre_resultats": len(candidats),
            "resultats": candidats,
        })


class ItineraireView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        depart = request.data.get("depart")
        arrivee = request.data.get("arrivee")

        if not isinstance(depart, dict) or not isinstance(arrivee, dict):
            return Response(
                {
                    "detail": (
                        "Les champs depart et arrivee doivent contenir "
                        "latitude et longitude."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        def lire_point(point):
            latitude = coordonnee_valide(
                point.get("latitude"), -90, 90
            )
            longitude = coordonnee_valide(
                point.get("longitude"), -180, 180
            )

            if latitude is None or longitude is None:
                return None

            return latitude, longitude

        point_depart = lire_point(depart)
        point_arrivee = lire_point(arrivee)

        if point_depart is None or point_arrivee is None:
            return Response(
                {
                    "detail": (
                        "Coordonnées GPS invalides. "
                        "Vérifie les latitudes et longitudes."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        lat_d, lon_d = point_depart
        lat_a, lon_a = point_arrivee

        # OSRM attend longitude,latitude pour chaque point.
        coordonnees = f"{lon_d},{lat_d};{lon_a},{lat_a}"

        try:
            response = requests.get(
                f"{OSRM_URL}/{coordonnees}",
                params={
                    "overview": "full",
                    "geometries": "geojson",
                    "steps": "false",
                },
                headers={"User-Agent": USER_AGENT},
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()

        except (requests.RequestException, ValueError):
            return Response(
                {
                    "detail": (
                        "Le calcul d'itinéraire est momentanément "
                        "indisponible."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        routes = data.get("routes", [])

        if data.get("code") != "Ok" or not routes:
            return Response(
                {
                    "detail": (
                        "Aucun itinéraire routier n'a été trouvé "
                        "entre ces deux points."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        route = routes[0]

        return Response({
            "distance_metres": route["distance"],
            "duree_secondes": route["duration"],
            "distance_km": round(route["distance"] / 1000, 2),
            "duree_minutes": round(route["duration"] / 60),
            "geometry": route["geometry"],
            "source": "OSRM",
        })
