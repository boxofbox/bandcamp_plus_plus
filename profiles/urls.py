from django.urls import path

from .views import ProfileListView, PurchaseListView

urlpatterns = [
    path("", ProfileListView.as_view(), name="profile_list"),
    path("", PurchaseListView.as_view(), name="purchase_list"),
]
