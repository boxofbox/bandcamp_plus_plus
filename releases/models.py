from django.db import models

class LabelBand(models.Model):
    id = models.BigIntegerField(primary_key=True)
    name = models.TextField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    img_id = models.BigIntegerField(null=True, blank=True)

class Release(models.Model):
    id = models.BigIntegerField(primary_key=True)

    ALBUM = 'a'
    TRACK = 't'
    subclass = models.CharField(
        max_length=1,
        choices=[(ALBUM, 'album'),(TRACK, 'track')],
        default=ALBUM
        )
    
    title = models.TextField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    img_url = models.URLField(null=True, blank=True)
    price = models.TextField(null=True, blank=True)
    release_date = models.DateTimeField(null=True, blank=True)
    last_viewed_as_preorder = models.BooleanField(null=True, blank=True)
    
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

    artist_name = models.TextField(null=True, blank=True)

class Track(Release):
    album = models.ForeignKey(
                                Release, 
                                related_name='tracks',
                                blank=True,
                                null=True,
                                on_delete=models.CASCADE)
    mp3 = models.URLField(null=True, blank=True)
    track_number = models.IntegerField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True)
