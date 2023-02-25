from django.db import models

from releases.models import Release, LabelBand
class Profile(models.Model):
    id = models.BigIntegerField(primary_key=True)
    username = models.TextField(null=True, blank=True)
    name = models.TextField(null=True, blank=True)
    img_url = models.URLField(null=True, blank=True)
    following_fans = models.ManyToManyField("self", related_name="followers", symmetrical=False, blank=True)
    following_labelbands = models.ManyToManyField(LabelBand, related_name="fans", blank=True)
    
    purchases = models.ManyToManyField(
                                        Release, 
                                        through='Purchase',
                                        through_fields = ('profile','release'),
                                        related_name='purchased_by',
                                        blank=True
                                        )

class Purchase(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    release = models.ForeignKey(Release, on_delete=models.CASCADE)
    date = models.DateTimeField(null=True, blank=True)