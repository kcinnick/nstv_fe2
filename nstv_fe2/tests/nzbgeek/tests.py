import datetime
import os

from bs4 import BeautifulSoup
from django.test import TestCase

from nstv_fe2.models import Episode, Show
from nstv_fe2.nzbg import NZBGeek, SearchResult
from nstv_fe2.views import download_episode


class NZBGeekTests(TestCase):
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

    def test_get_nzb_no_results_found_prints_error(self):
        show = Show.objects.get(id=1)
        episode_title = 'This Episode Did Not Exist'
        downloaded = self.nzbg.get_nzb(show=show, episode_title=episode_title)
        self.assertEqual(downloaded, False)

    def test_get_nzb_no_season_or_episode_number_raises_error(self):
        show = Show.objects.get(id=1)
        with self.assertRaises(AttributeError):
            self.nzbg.get_nzb(show=show, episode_title=False, )

    def test_nzbgeek_search_result(self):
        url = self.nzbg._build_search_url(
            show=Show.objects.get(title='Seinfeld'),
            episode_number=6,
            season_number=3,
        )
        print(f"\nRequesting {url}")
        r = self.nzbg.session.get(url)

        soup = BeautifulSoup(r.content, "html.parser")
        results = soup.find_all("table", class_="releases")
        parsed_result = [SearchResult(i) for i in results][0]
        self.assertIn(
            'Seinfeld', parsed_result.title
        )
        self.assertIn('S03E06', parsed_result.title)
        self.assertIn('Seinfeld', str(parsed_result))

    def test_nzbgeek_strict_search_with_no_results_raises_valueerror(self):
        show = Show.objects.get(id=1)
        with self.assertRaises(ValueError):
            self.nzbg.get_nzb(show=show, episode_title='This Episode Doesn\'t Exist', strict=True)
        return


class DownloadEpisodeTests(TestCase):
    def setUp(self):
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

    def test_download_episode(self):
        response = self.client.get(
            'http://localhost:8000/shows/1/season/3/episode/6/nzbgeek'
        )
        self.assertEqual(response.status_code, 302)

    def test_download_episode_that_does_not_exist_returns_redirect(self):
        response = download_episode('', show_id=1, episode_title='This episode never existed.')
        self.assertEqual(response.status_code, 302)