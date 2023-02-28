from django.views.generic import ListView

from .models import Bin, RecentFanPurchase, RecentLabelBandRelease, Issue

class BinListView(ListView):
    model = Bin
    template_name = "bins/bin_list.html"

class RecentFanPurchaseListView(ListView):
    model = RecentFanPurchase
    template_name = "bins/recentfanpurchase_list.html"

class RecentLabelBandReleaseListView(ListView):
    model = RecentLabelBandRelease
    template_name = "bins/recentlabelbandrelease_list.html"

class IssueListView(ListView):
    model = Issue
    template_name = "bins/issue_list.html"