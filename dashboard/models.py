from django.db import models

# Create your models here.
from profiles.models import Profile

class DashboardSettings(models.Model):
    lock = models.CharField(max_length=1, null=False, primary_key='True', default='X')
    delay_time = models.FloatField(default=1.0)
    base_profile = models.ForeignKey(Profile, null=True, blank=True, on_delete=models.SET_NULL)
    max_profile_depth = models.IntegerField(default=0)
    main_update_task_run_once = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.pk = 'X'
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk='X')
        # set the run once flag to false on startup for our main celery update task
        if not created:
            obj.main_update_task_run_once = False
            obj.save(update_fields=["main_update_task_run_once"])
        return obj