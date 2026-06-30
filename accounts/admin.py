from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('站点资料', {'fields': ('nickname',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('站点资料', {'fields': ('nickname',)}),
    )
    list_display = ('username', 'nickname', 'email', 'is_staff', 'is_active')
    search_fields = ('username', 'nickname', 'email')
