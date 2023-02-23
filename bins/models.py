from django.db import models

class Bin(models.Model):
    # m2m releases
    # sort ordering key
    # date added
    pass


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