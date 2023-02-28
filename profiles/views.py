from django.views.generic import ListView

from .models import Profile, Purchase

class ProfileListView(ListView):
    model = Profile
    template_name = "profiles/profile_list.html"

class PurchaseListView(ListView):
    model = Purchase
    template_name = "profiles/purchase_list.html"