import datetime

from django.test import TestCase

from nstv_fe2.models import Episode, Show
from nstv_fe2.nzbg import NZBGeek


class ShowsIndexViewTests(TestCase):
    def setUp(self):
        self.nzbg = NZBGeek()
        self.nzbg.login()
        Show.objects.create(
            title="Seinfeld",
            gid=79169,
        )
        Episode.objects.create(
            title="The Parking Garage",
            season=3,
            number=6,
            original_air_date=datetime.date(1991, 10, 31),
            show=Show.objects.get(title="Seinfeld"),
        )

    def test_shows_index(self):
        response = self.client.get('http://localhost:8000')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Seinfeld")
        shows = Show.objects.all()
        self.assertQuerysetEqual(response.context['shows'].order_by('id'), shows.order_by('id'))


class ShowViewTests(TestCase):
    def setUp(self):
        self.nzbg = NZBGeek()
        self.nzbg.login()
        Show.objects.create(
            id=1,
            title="Seinfeld",
            gid=79169
        )
        Episode.objects.create(
            id=1,
            title="The Parking Garage",
            season=3,
            number=6,
            original_air_date=datetime.date(1991, 10, 31),
            show=Show.objects.get(title="Seinfeld"),
        )

    def test_show_view(self):
        """
        If no questions exist, an appropriate message is displayed.
        """
        response = self.client.get('http://localhost:8000/shows/1')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Seinfeld")
        show = Show.objects.get(id=1)
        show_episodes = Episode.objects.filter(show=show)
        self.assertEqual(response.context['show'], show)
        self.assertQuerysetEqual(response.context['show_episodes'], show_episodes)

    def test_update_downloaded_record_for_episodes_in_show(self):
        return
        #  TODO: finish this test

    def test_get_outstanding_season_episode_numbers_continues_if_invalid_episode_title(self):
        Episode.objects.create(
            title='',
            season=None,
            id=2
        )
        response = self.client.get('http://localhost:8000/get_outstanding_season_episode_numbers')
        self.assertEqual(response.status_code, 302)

    def test_get_outstanding_season_episode_numbers_continues_if_no_result_for_show(self):
        show = Show.objects.create(title='The Fake Show', id=2)
        Episode.objects.create(
            title='This episode does not exist.',
            season=None,
            id=2,
            show=show,
        )
        response = self.client.get('http://localhost:8000/get_outstanding_season_episode_numbers')
        self.assertEqual(response.status_code, 302)


    def test_get_outstanding_season_episode_numbers_continues_if_no_title_for_show(self):
        show = Show.objects.create(title='', id=2)
        Episode.objects.create(
            title='This episode does not exist.',
            season=None,
            id=2,
            show=show,
        )
        response = self.client.get('http://localhost:8000/get_outstanding_season_episode_numbers')
        self.assertEqual(response.status_code, 302)


