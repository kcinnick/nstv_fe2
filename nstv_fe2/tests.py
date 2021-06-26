import datetime

from django.test import TestCase
from .models import Episode, Show


class EpisodeTestCase(TestCase):
    def setUp(self):
        Show.objects.create(
            id=1,
            title='Seinfeld',
        )
        Episode.objects.create(
            id=1,
            title="The Parking Garage",
            season=3,
            number=6,
            original_air_date=datetime.date(1991, 10, 31),
            show=Show.objects.get(title='Seinfeld', )
        )

    def test_episode_belongs_to_show(self):
        """Episodes belong to the right show."""
        episode = Episode.objects.get(title="The Parking Garage")
        self.assertEqual(episode.season, 3)
        self.assertEqual(episode.show.title, 'Seinfeld')


class ShowTestCase(TestCase):
    def setUp(self):
        Show.objects.create(
            id=1,
            title='Seinfeld',
        )
        Episode.objects.create(
            id=1,
            title="The Parking Garage",
            season=3,
            number=6,
            original_air_date=datetime.date(1991, 10, 31),
            show=Show.objects.get(title='Seinfeld', )
        )

    def test_show_get_episode(self):
        show = Show.objects.get(title='Seinfeld')
        seinfeld_episodes = Episode.objects.filter(show=show)
        seinfeld_episodes.filter(title='The Parking Garage').exists()