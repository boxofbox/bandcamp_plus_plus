from django.urls import path, re_path

from .views import pre_dashboard_wrapper, post_dashboard_settings, dashboard_wrapper, \
            progress_view, progress_view_abort, progress_view_run, progress_view_reset, \
            dashboard_home, main_last_completed_date, dashboard_settings, dashboard_settings_wrapper, \
            base_profile_info, dashboard_d3test, dashboard_d3test_wrapper

urlpatterns = [
    path("", pre_dashboard_wrapper, name="dashboard_wrapper"),
    
    path("dashboard_settings_update", post_dashboard_settings, name="dashboardsettingsupdate"),

    # AJAX CONTENT PANELS
    path("dashboard/ajax/dashboard_home", dashboard_home, name="dashboardajaxpromptupdate"),
    path("dashboard/ajax/settings", dashboard_settings, name="dashboardajaxsettings"),
    path("dashboard/ajax/d3test", dashboard_d3test, name="dashboardajaxd3test"),
    

    # REWRAPPED CONTEXTS
    re_path(r"dashboard/?$", dashboard_wrapper, name="dashboard"),  
    path("dashboard/settings", dashboard_settings_wrapper, name="dashboardsettingswrapper"),
    path("dashboard/d3test", dashboard_d3test_wrapper, name="dashboardd3testwrapper"),  

    # UTILITIES
    path("dashboard/main_last_completed_date", main_last_completed_date, name="dashboardmainlastcompleteddate"),
    path("dashboard/base_profile_info", base_profile_info, name="dashboardbaseprofileinfo"),

    # DEMO/DEBUG TODO REMOVE
    path("progtest", progress_view, name="progview"),
    path("progtest/abort", progress_view_abort, name="progviewabort"),
    path("progtest/run", progress_view_run, name="progviewrun"),
    path("progtest/reset", progress_view_reset, name="progviewreset"),
    
]
