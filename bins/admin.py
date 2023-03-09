from django.contrib import admin

from .models import Bin, Issue, RecentFanPurchase, RecentLabelBandRelease, ReleaseAcquiredOutsideBandcamp, \
                        NewFollowers, NewFollowingFans_Base, NewFollowingFans_Network, NewFollowingLabelBands

class BinAdmin(admin.ModelAdmin):
    fields = ['name', 'sort_key', 'date_updated', 'related',]
    list_display = ('name', 'sort_key', 'date_updated') 

class IssueAdmin(admin.ModelAdmin):
    fields = ['item_id', 'flag', 'note']
    list_display = ('item_id', 'flag', 'note') 

class RecentFanPurchaseAdmin(admin.ModelAdmin):
    fields = ['release', 'recently_bought_by', 'most_recent_purchase_date',]
    list_display = ('release', 'most_recent_purchase_date') 

class RecentLabelBandReleaseAdmin(admin.ModelAdmin):
    fields = ['release', 'recently_released_by', 'release_date']
    list_display = ('release', 'release_date') 

class ReleaseAcquiredOutsideBandcampAdmin(admin.ModelAdmin):
    fields = ['release']
    list_display = ('release',)

class NewFollowersAdmin(admin.ModelAdmin):
    pass

class NewFollowingFans_BaseAdmin(admin.ModelAdmin):
    pass

class NewFollowingFans_NetworkAdmin(admin.ModelAdmin):
    pass

class NewFollowingLabelBandsAdmin(admin.ModelAdmin):
    pass

admin.site.register(Bin, BinAdmin)
admin.site.register(Issue, IssueAdmin)
admin.site.register(RecentFanPurchase, RecentFanPurchaseAdmin)
admin.site.register(RecentLabelBandRelease, RecentLabelBandReleaseAdmin)
admin.site.register(ReleaseAcquiredOutsideBandcamp, ReleaseAcquiredOutsideBandcampAdmin)

admin.site.register(NewFollowers, NewFollowersAdmin)
admin.site.register(NewFollowingFans_Base, NewFollowingFans_BaseAdmin)
admin.site.register(NewFollowingFans_Network, NewFollowingFans_NetworkAdmin)
admin.site.register(NewFollowingLabelBands, NewFollowingLabelBandsAdmin)