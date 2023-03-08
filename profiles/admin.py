from django.contrib import admin

from .models import Profile, Purchase

class ProfileAdmin(admin.ModelAdmin):
    fields = ['id', 'username', 'name', 'img_id']
    list_display = ('id', 'username', 'name', 'img_id') 

class PurchaseAdmin(admin.ModelAdmin):
    fields = ['profile', 'release', 'date']
    list_display = ('profile', 'release', 'date')

admin.site.register(Profile, ProfileAdmin)
admin.site.register(Purchase, PurchaseAdmin)