from django.db import models

from releases.models import Release, LabelBand
from profiles.models import Profile


class Bin(models.Model):    
    name = models.TextField(null=True, blank=True)
    sort_key = models.TextField(null=True, blank=True)
    date_updated = models.DateTimeField(null=True, blank=True)
    releases = models.ManyToManyField(
                                        Release,
                                        blank=True,
                                        related_name='in_bins',
                                    )


class RecentFanPurchase(models.Model):
    release = models.OneToOneField(Release, on_delete=models.CASCADE)
    recently_bought_by = models.ManyToManyField(Profile)
    most_recent_purchase_date = models.DateTimeField(null=True, blank=True)
    seen_before = models.BooleanField(default=False)


class RecentLabelBandRelease(models.Model):
    release = models.OneToOneField(Release, on_delete=models.CASCADE)
    recently_released_by = models.ManyToManyField(LabelBand)
    release_date = models.DateTimeField(null=True, blank=True)
    seen_before = models.BooleanField(default=False)


class ReleaseAcquiredOutsideBandcamp(models.Model):
    release = models.OneToOneField(Release, on_delete=models.CASCADE)


class NewFollowers(models.Model):
    follower = models.OneToOneField(Profile, on_delete=models.CASCADE)


class NewFollowingFans(models.Model):
    following_fan = models.OneToOneField(Profile, on_delete=models.CASCADE)


class NewFollowingLabelBands(models.Model):
    following_fan = models.OneToOneField(LabelBand, on_delete=models.CASCADE)


class Issue(models.Model):
    item_id = models.BigIntegerField(null=True, blank=True)

    ALBUM = 'a'
    TRACK = 't'
    PROFILE = 'p'
    LABELBAND = 'l'
    OTHER = 'o'
    flag = models.CharField(
        max_length=1,
        choices=[
            (ALBUM, 'album'),
            (TRACK, 'track'),
            (PROFILE, 'profile'),
            (LABELBAND, 'labelband'),
            (OTHER, 'other')
            ],
        default=ALBUM
        )
    
    note = models.TextField(null=True, blank=True)    