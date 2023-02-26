from django.urls import path

from .views import DashboardView, progress_view, progress_view_abort, progress_view_run

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("progtest", progress_view, name="progview"),
    path("progtest/abort", progress_view_abort, name="progviewabort"),
    path("progtest/run", progress_view_run, name="progviewrun"),
    
]
