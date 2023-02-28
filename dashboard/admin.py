from django.contrib import admin

from .models import DashboardSettings

class DashboardAdmin(admin.ModelAdmin):
    fields = ['delay_time', 'base_profile', 'max_profile_depth', 'main_update_last_completed',]
    list_display = ('delay_time', 'base_profile', 'max_profile_depth', 'main_update_last_completed',) 


admin.site.register(DashboardSettings, DashboardAdmin)
