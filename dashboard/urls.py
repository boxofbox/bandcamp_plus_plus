from django.urls import path

from .views import pre_dashboard_wrapper, post_dashboard_settings, dashboard_wrapper, \
            progress_view, progress_view_abort, progress_view_run, progress_view_reset, \
            prompt_update, main_last_completed_date, dashboard_settings, dashboard_settings_wrapper

urlpatterns = [
    path("", pre_dashboard_wrapper, name="dashboard_wrapper"),
    
    path("dashboard_settings_update", post_dashboard_settings, name="dashboardsettingsupdate"),

    # AJAX CONTENT PANELS
    path("dashboard/ajax/prompt_update", prompt_update, name="dashboardajaxpromptupdate"),
    path("dashboard/ajax/settings", dashboard_settings, name="dashboardajaxsettings"),

    # REWRAPPED CONTEXTS
    path("dashboard", dashboard_wrapper, name="dashboard"),  
    path("dashboard/settings", dashboard_settings_wrapper, name="dashboardsettingswrapper"),  



    path("dashboard/main_last_completed_date", main_last_completed_date, name="dashboardmainlastcompleteddate"),
    path("progtest", progress_view, name="progview"),
    path("progtest/abort", progress_view_abort, name="progviewabort"),
    path("progtest/run", progress_view_run, name="progviewrun"),
    path("progtest/reset", progress_view_reset, name="progviewreset"),
    
]
