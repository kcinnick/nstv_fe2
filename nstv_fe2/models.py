from django.db import models


class Show(models.Model):
    title = models.TextField(unique=True)
    gid = models.IntegerField(unique=True, null=True)  # this is the geek ID, used for easier downloading on NZBGeek


class Episode(models.Model):
    title = models.TextField(unique=True)
    season = models.IntegerField(null=True)
    number = models.IntegerField(null=True)
    original_air_date = models.DateField(null=True)

    show = models.ForeignKey("Show", on_delete=models.CASCADE, null=True)

    downloaded = models.BooleanField(default=False)
