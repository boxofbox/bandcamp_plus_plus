from django.contrib import admin

from .models import Bin, Issue, RecentFanPurchase, RecentLabelbandRelease

admin.site.register(Bin)
admin.site.register(Issue)
admin.site.register(RecentFanPurchase)
admin.site.register(RecentLabelbandRelease)