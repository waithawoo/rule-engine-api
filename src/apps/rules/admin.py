from django.contrib import admin

from .models import Rule


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_by', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_by', 'created_at', 'updated_at')
