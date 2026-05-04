from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.db import IntegrityError

from .models import User, UserProfile


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Inventory Access', {'fields': ('role',)}),
    )

    def log_deletions(self, request, queryset):
        """
        Avoid hard failure when legacy admin log FK still points to old auth_user.
        This keeps delete action functional after custom user-model migration drift.
        """
        try:
            super().log_deletions(request, queryset)
        except IntegrityError:
            pass


admin.site.register(UserProfile)
