import datetime
import os

from django.test import TestCase

from nstv_fe2.models import Episode, Show
from nstv_fe2.nzbg import NZBGeek


class EpisodeTestCase(TestCase):
    def setUp(self):
        Show.objects.create(id=1, title="Seinfeld")
        Episode.objects.create(
            id=1,
            title="The Parking Garage",
            season=3,
            number=6,
            original_air_date=datetime.date(1991, 10, 31),
            show=Show.objects.get(title="Seinfeld"),
        )

    def test_episode_belongs_to_show(self):
        """Episodes belong to the right show."""
        episode = Episode.objects.get(title="The Parking Garage")
        self.assertEqual(episode.season, 3)
        self.assertEqual(episode.show.title, "Seinfeld")


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


class NZBGeekTestCase(TestCase):
    def setUp(self):
        self.nzbg = NZBGeek()
        self.nzbg.login()
        Show.objects.create(id=1, title="Seinfeld", gid=79169)
        Episode.objects.create(
            id=1,
            title="The Parking Garage",
            season=3,
            number=6,
            original_air_date=datetime.date(1991, 10, 31),
            show=Show.objects.get(title="Seinfeld"),
        )

    def test_assert_logged_in(self):
        r = self.nzbg.session.get("https://nzbgeek.info/dashboard.php")
        assert os.getenv("NZBGEEK_USERNAME") in str(r.content)

    def test_assert_login_bounces_if_logged_in(self):
        self.nzbg.login()

    def test_get_nzb_with_season_and_episode_number(self):
        show = Show.objects.get(id=1)
        season_number = 3
        episode_number = 6
        self.nzbg.get_nzb(
            show=show,
            season_number=season_number,
            episode_number=episode_number,
        )

    def test_get_nzb_no_results_found(self):
        show = Show.objects.get(id=1)
        episode_title = 'This Episode Did Not Exist'
        self.nzbg.get_nzb(show=show, episode_title=episode_title)

    def test_get_nzb_no_season_or_episode_number_raises_error(self):
        show = Show.objects.get(id=1)
        with self.assertRaises(AttributeError):
            self.nzbg.get_nzb(show=show, episode_title=False, )


class ShowsIndexViewTests(TestCase):
    def setUp(self):
        self.nzbg = NZBGeek()
        self.nzbg.login()
        Show.objects.create(id=1, title="Seinfeld", gid=79169)
        Episode.objects.create(
            id=1,
            title="The Parking Garage",
            season=3,
            number=6,
            original_air_date=datetime.date(1991, 10, 31),
            show=Show.objects.get(title="Seinfeld"),
        )

    def test_shows_index(self):
        """
        If no questions exist, an appropriate message is displayed.
        """
        response = self.client.get('http://localhost:8000')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Seinfeld")
        shows = Show.objects.all()
        self.assertQuerysetEqual(response.context['shows'], shows)
