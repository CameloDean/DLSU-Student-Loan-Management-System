from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_delete


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    id_number = models.CharField(max_length=8, blank=True, primary_key=True)
    college = models.CharField(max_length=6, blank=True)
    course = models.CharField(max_length=10, blank=True)
    cellphone_number = models.CharField(max_length=11, blank=True)
    level = models.CharField(max_length=13, blank=True)

    def __str__(self):
        return self.last_name + ' ' + self.first_name


@receiver(post_delete, sender=Student)
def post_delete_user(sender, instance, *args, **kwargs):
    if instance.user:  # just in case user is not specified
        instance.user.delete()
