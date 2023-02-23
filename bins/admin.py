from django.contrib import admin

from .models import Bin, Issue

admin.site.register(Bin)
admin.site.register(Issue)