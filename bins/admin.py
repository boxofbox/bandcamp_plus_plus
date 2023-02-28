from django.contrib import admin

from .models import Bin, Issue, RecentFanPurchase, RecentLabelBandRelease

class BinAdmin(admin.ModelAdmin):
    fields = ['name', 'sort_key', 'date_updated', 'related',]
    list_display = ('name', 'sort_key', 'date_updated') 

class IssueAdmin(admin.ModelAdmin):
    fields = ['item_id', 'flag', 'note']
    list_display = ('item_id', 'flag', 'note') 

class RecentFanPurchaseAdmin(admin.ModelAdmin):
    fields = ['release', 'recently_bought_by', 'most_recent_purchase_date', 'seen_before',]
    list_display = ('release', 'most_recent_purchase_date', 'seen_before') 

class RecentLabelBandReleaseAdmin(admin.ModelAdmin):
    fields = ['release', 'recently_released_by', 'release_date', 'seen_before',]
    list_display = ('release', 'release_date', 'seen_before') 


admin.site.register(Bin, BinAdmin)
admin.site.register(Issue, IssueAdmin)
admin.site.register(RecentFanPurchase, RecentFanPurchaseAdmin)
admin.site.register(RecentLabelBandRelease, RecentLabelBandReleaseAdmin)