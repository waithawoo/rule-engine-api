from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'role', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'role')
    search_fields = ('email',)
    ordering = ('email',)
    readonly_fields = ('created_at', 'updated_at', 'last_login')
    
    fieldsets = (
        (('Personal info'), {'fields': ('email',)}),
        (('Role'), {'fields': ('role',)}),
        (('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (('DateTimes'), {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role'),
        }),
    )
    
