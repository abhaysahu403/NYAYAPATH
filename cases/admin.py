from django.contrib import admin
from .models import Case, CaseEvent, CaseParty, Hearing


class CasePartyInline(admin.TabularInline):
    model = CaseParty
    extra = 0


class CaseEventInline(admin.TabularInline):
    model = CaseEvent
    extra = 0
    fields = ["event_type", "event_date", "title", "data_origin"]


class HearingInline(admin.TabularInline):
    model = Hearing
    extra = 0


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ["case_title", "cnr_number", "status", "state", "district", "user", "is_demo_data", "created_at"]
    list_filter = ["status", "case_type", "state", "is_demo_data"]
    search_fields = ["cnr_number", "case_number", "case_title", "user__email"]
    raw_id_fields = ["user", "court"]
    inlines = [CasePartyInline, CaseEventInline, HearingInline]
