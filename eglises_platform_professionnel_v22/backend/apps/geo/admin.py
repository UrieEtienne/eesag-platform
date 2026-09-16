from django.contrib import admin
from .models import Region, Prefecture, District, Commune

admin.site.register(Region)
admin.site.register(Prefecture)
admin.site.register(District)
admin.site.register(Commune)
