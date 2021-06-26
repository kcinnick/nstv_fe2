from django.db import models


class Show(models.Model):
    id = models.IntegerField(primary_key=True, unique=True, auto_created=True)
    title = models.TextField()


class Episode(models.Model):
    id = models.IntegerField(primary_key=True, unique=True, auto_created=True)
    title = models.TextField()
    season = models.IntegerField()
    number = models.IntegerField()
    original_air_date = models.DateField()

    show = models.ForeignKey("Show", on_delete=models.CASCADE, null=True)
