from django.db import models

from releases.models import Release, LabelBand
from profiles.models import Profile
class Bin(models.Model):    
    name = models.TextField
    sort_key = models.TextField
    date_updated = models.DateTimeField
    releases = models.ManyToManyField(
                                        Release,
                                        blank=True,
                                        related_name='in_bins',
                                    )

class RecentFanPurchase(models.Model):
    release = models.ForeignKey(Release, on_delete=models.CASCADE)
    recently_bought_by = models.ManyToManyField(Profile)
    date_updated = models.DateTimeField
    seen_before = models.BooleanField

class RecentLabelbandRelease(models.Model):
    release = models.ForeignKey(Release, on_delete=models.CASCADE)
    recently_released_by = models.ManyToManyField(LabelBand)
    date_updated = models.DateTimeField
    seen_before = models.BooleanField

class Issue(models.Model):
    item_id = models.BigIntegerField

    ALBUM = 'a'
    TRACK = 't'
    PROFILE = 'p'
    LABELBAND = 'l'
    flag = models.CharField(
        max_length=1,
        choices=[
            (ALBUM, 'album'),
            (TRACK, 'track'),
            (PROFILE, 'profile'),
            (LABELBAND, 'labelband')
            ],
        default=ALBUM
        )
    
    note = models.TextField    