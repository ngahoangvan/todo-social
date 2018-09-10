from django.db import models
from django.contrib.auth.models import User
from django.db.models import signals
from tastypie.models import create_api_key

# Create your models here.
signals.post_save.connect(create_api_key, sender=User)


class Profile(models.Model):
    other_name = models.CharField(max_length=255, blank=True)
    birthday = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=255, blank=True)
    photo_url = models.CharField(max_length=255, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.get_full_name()


class Relationship(models.Model):
    STATUS_IN_RELATIONSHIP = (
        (0, 'pending'),
        (1, 'accepted'),
        (2, 'declined'),
        (3, 'blocked'),
    )
    user_one = models.ForeignKey(User,
                                 on_delete=models.CASCADE,
                                 related_name='user_one')
    user_two = models.ForeignKey(User,
                                 on_delete=models.CASCADE,
                                 related_name='user_two')
    status = models.IntegerField(choices=STATUS_IN_RELATIONSHIP, default=0)
    action_user_id = models.IntegerField()
