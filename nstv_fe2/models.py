from django.db import models


class Show(models.Model):
    title = models.TextField(unique=True)
    gid = models.IntegerField(unique=True, null=True)


class Episode(models.Model):
    title = models.TextField(unique=True)
    season = models.IntegerField(null=True)
    number = models.IntegerField(null=True)
    original_air_date = models.DateField()

    show = models.ForeignKey("Show", on_delete=models.CASCADE, null=True)
