import datetime
import os

from bs4 import BeautifulSoup
from django.test import TestCase

from nstv_fe2.models import Episode, Show
from nstv_fe2.nzbg import NZBGeek, SearchResult


class ShowTestCase(TestCase):
    def setUp(self):
        Show.objects.create(id=1, title="Seinfeld", gid=79169)
        Episode.objects.create(
            id=1,
            title="The Parking Garage",
            season=3,
            number=6,
            original_air_date=datetime.date(1991, 10, 31),
            show=Show.objects.get(title="Seinfeld"),
        )

    def test_show_get_episode(self):
        show = Show.objects.get(title="Seinfeld")
        seinfeld_episodes = Episode.objects.filter(show=show)
        seinfeld_episodes.filter(title="The Parking Garage").exists()
