from django.urls import path

from .views import LabelBandListView, ReleaseListView, TrackListView, AlbumListView

urlpatterns = [
    path("labelbands", LabelBandListView.as_view(), name="labelband_list"),
    path("", ReleaseListView.as_view(), name="release_list"),
    path("tracks", TrackListView.as_view(), name="track_list"),
    path("albums", AlbumListView.as_view(), name="album_list"),
]