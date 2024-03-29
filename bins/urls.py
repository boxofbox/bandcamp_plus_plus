from django.urls import path

from .views import BinListView, RecentFanPurchaseListView, RecentLabelBandReleaseListView, IssueListView, ReleaseAcquiredOutsideBandcampListView

urlpatterns = [
    path("", BinListView.as_view(), name="bin_list"),
    path("recentfanpurchases", RecentFanPurchaseListView.as_view(), name="recentfanpurchaselist_list"),
    path("recentbandlabelreleases", RecentLabelBandReleaseListView.as_view(), name="recentlabelbandrelease_list"),
    path("issues", IssueListView.as_view(), name="issue_list"),
    path("releasesacquiredoutsidebandcamp", ReleaseAcquiredOutsideBandcampListView.as_view(), name="releasesacquiredoutsidebandcamp_list"),
]
