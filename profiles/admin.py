from django.contrib import admin

from .models import Profile, Purchase

class ProfileAdmin(admin.ModelAdmin):
    fields = ['id', 'username', 'name', 'img_url', 'followers', 'following_labelbands']
    list_display = ('id', 'username', 'name') 

admin.site.register(Profile, ProfileAdmin)
admin.site.register(Purchase)