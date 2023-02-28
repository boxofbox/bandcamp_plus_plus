from django.urls import path

from .views import dashboard, post_dashboard_settings, progress_view, progress_view_abort, progress_view_run, progress_view_reset

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("dashboard_settings_update", post_dashboard_settings, name="dashboardsettingsupdate"),


    path("progtest", progress_view, name="progview"),
    path("progtest/abort", progress_view_abort, name="progviewabort"),
    path("progtest/run", progress_view_run, name="progviewrun"),
    path("progtest/reset", progress_view_reset, name="progviewreset"),
    
]
