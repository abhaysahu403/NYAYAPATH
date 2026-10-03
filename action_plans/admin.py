from django.contrib import admin
from .models import ActionPlan, ActionStep

class ActionStepInline(admin.TabularInline):
    model = ActionStep
    extra = 0
    fields = ["step_number", "title", "kind", "difficulty", "status"]

@admin.register(ActionPlan)
class ActionPlanAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "status", "language", "created_at"]
    list_filter = ["status", "language"]
    raw_id_fields = ["user", "case"]
    inlines = [ActionStepInline]
