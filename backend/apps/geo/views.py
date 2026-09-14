from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import EstSuperAdminNationalOuPlus
from .models import Region, Prefecture, District, Commune
from .serializers import RegionSerializer, PrefectureSerializer, DistrictSerializer, CommuneSerializer


class LecturePourTousEcriturePourNationalMixin:
    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticated()]
        return [EstSuperAdminNationalOuPlus()]


class RegionViewSet(LecturePourTousEcriturePourNationalMixin, viewsets.ModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer


class PrefectureViewSet(LecturePourTousEcriturePourNationalMixin, viewsets.ModelViewSet):
    queryset = Prefecture.objects.select_related("region").all()
    serializer_class = PrefectureSerializer
    filterset_fields = ["region"]


class DistrictViewSet(LecturePourTousEcriturePourNationalMixin, viewsets.ModelViewSet):
    queryset = District.objects.select_related("prefecture").all()
    serializer_class = DistrictSerializer
    filterset_fields = ["prefecture"]


class CommuneViewSet(LecturePourTousEcriturePourNationalMixin, viewsets.ModelViewSet):
    queryset = Commune.objects.select_related("district").all()
    serializer_class = CommuneSerializer
    filterset_fields = ["district"]
