from django.contrib import admin

from .models import Release, Track, LabelBand

admin.site.register(Release)
admin.site.register(Track)
admin.site.register(LabelBand)