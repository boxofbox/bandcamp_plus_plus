from django.db import models

class LabelBand(models.Model):
    id = models.BigIntegerField(primary_key=True)
    name = models.TextField
    url = models.URLField
    img_id = models.BigIntegerField

class Release(models.Model):
    item_id = models.BigIntegerField(primary_key=True)

    ALBUM = 'a'
    TRACK = 't'
    subclass = models.CharField(
        max_length=1,
        choices=[(ALBUM, 'album'),(TRACK, 'track')],
        default=ALBUM
        )
    
    title = models.TextField
    url = models.URLField
    img_url = models.URLField
    price = models.TextField
    release_date = models.DateTimeField
    
    artist_id = models.ForeignKey(
                                    LabelBand, 
                                    related_name="releases", 
                                    blank=True,
                                    null=True,
                                    on_delete=models.PROTECT
                                    )
    selling_artist_id = models.ForeignKey(
                                    LabelBand, 
                                    related_name="selling_releases",
                                    blank=True,
                                    null=True,
                                    on_delete=models.PROTECT
                                    )

    artist_name = models.TextField

class Track(Release):
    album = models.ForeignKey(
                                Release, 
                                related_name='tracks',
                                blank=True,
                                null=True,
                                on_delete=models.CASCADE)
    mp3 = models.URLField
    track_number = models.IntegerField
    duration = models.FloatField
