from django.urls import path

from .views import DashboardView, progress_view

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("progtest", progress_view, name="progview")
]
