from django.contrib import admin
from .models import Court

@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ["name", "court_type", "state", "district", "active"]
    list_filter = ["court_type", "state", "active"]
    search_fields = ["name", "state", "district", "official_identifier"]
    ordering = ["state", "name"]
