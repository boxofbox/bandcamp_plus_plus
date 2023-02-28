from django.views.generic import ListView

from .models import LabelBand, Release, Track

class LabelBandListView(ListView):
    model = LabelBand
    template_name = "releases/labelband_list.html"

class ReleaseListView(ListView):
    model = Release
    template_name = "releases/release_list.html"

class TrackListView(ListView):
    model = Track
    template_name = "releases/track_list.html"

class AlbumListView(ListView):
    model = Release
    # TODO subfilter by albums
    template_name = "releases/album_list.html"