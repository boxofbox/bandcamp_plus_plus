from django.db import models

from releases.models import Release, LabelBand
class Profile(models.Model):
    id = models.BigIntegerField
    username = models.TextField
    name = models.TextField
    
    followers = models.ManyToManyField("self", symmetrical=False) # TODO check symmetric, related_name
    following_fans = models.ManyToManyField("self", symmetrical=False) # TODO check symmetric, related_name
    following_labelbands = models.ManyToManyField(LabelBand) # TODO related_name
    
    purchases = models.ManyToManyField(
                                        Release, 
                                        through='Purchase',
                                        through_fields = ('profile','release')
                                        )

class Purchase(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE) # TODO check delete, related_name
    release = models.ForeignKey(Release, on_delete=models.CASCADE) # TODO check delete, related_name
    date = models.DateTimeField