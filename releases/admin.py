from django.contrib import admin

from .models import Release, Track, LabelBand


class ReleaseAdmin(admin.ModelAdmin):
    fields = ['id', 'subclass', 'title', 'url', 'img_url', 'price', 'release_date', 'artist_id', 'artist_name', 'selling_artist_id',]
    list_display = ('id', 'title', 'artist_name', 'release_date') 

class TrackAdmin(admin.ModelAdmin):
    fields = ['id', 'subclass', 'title', 'url', 'img_id', 'price', 'release_date', 'artist_id', 'artist_name', 'selling_artist_id','album', 'mp3', 'track_number', 'duration']
    list_display = ('id', 'title', 'artist_name', 'release_date', 'album') 


class LabelBandAdmin(admin.ModelAdmin):
    fields = ['id', 'name', 'url', 'img_id']
    list_display = ('id', 'name', 'url', 'img_id') 


admin.site.register(Release, ReleaseAdmin)
admin.site.register(Track, TrackAdmin)
admin.site.register(LabelBand, LabelBandAdmin)