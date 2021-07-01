import datetime
import os

from bs4 import BeautifulSoup
from django.test import TestCase

from nstv_fe2.models import Episode, Show
from nstv_fe2.nzbg import NZBGeek, SearchResult
from nstv_fe2.tvtv_scraper import search_channel_listings, upload_channel_search_response


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

    def test_get_nzb_no_results_found_raises_error(self):
        show = Show.objects.get(id=1)
        episode_title = 'This Episode Did Not Exist'
        with self.assertRaises(ValueError):
            self.nzbg.get_nzb(show=show, episode_title=episode_title)

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


class TvtvScraperSearchChannelsTests(TestCase):
    def setUp(self):
        Show.objects.create(
            id=1,
            title="Seinfeld",
            gid=79169
        )
        self.start_date = (datetime.datetime.now() - datetime.timedelta(1)).strftime('%Y-%m-%d')
        self.end_date = datetime.datetime.now().strftime('%Y-%m-%d')

    def test_search_channels(self):
        json_response = search_channel_listings(
            start_channel=2, end_channel=29,
            start_date=self.start_date, end_date=self.end_date)
        expected_channel_list = [2, 3, 4, 5, 6, 7, 8, 9, 11, 15, 16,
                                 17, 20, 22, 23, 24, 25, 27, 28, 29]
        actual_channel_list = []
        for item in json_response:
            actual_channel_list.append(item['channel']['channelNumber'])
        assert expected_channel_list == actual_channel_list

    def test_assert_error_is_raised_on_invalid_search(self):
        with self.assertRaises(ValueError):
            search_channel_listings(
                start_channel=44,
                end_channel=12,
                start_date='2021-05-01',
                end_date='2021-05-02',
            )


class TvtvScraperParseChannelSearchResponseTests(TestCase):
    def setUp(self):
        start_date = (datetime.datetime.now() - datetime.timedelta(1)).strftime('%Y-%m-%d')
        end_date = datetime.datetime.now().strftime('%Y-%m-%d')
        self.json_response = search_channel_listings(
            start_channel=2, end_channel=29,
            start_date=start_date, end_date=end_date)

    def test_parse_channel_search_response(self):
        upload_channel_search_response(self.json_response)
        #  TODO: this isn't a good test


class TvtvScraperUpdateDbTests(TestCase):
    def setUp(self) -> None:
        start_date = (datetime.datetime.now() - datetime.timedelta(1)).strftime('%Y-%m-%d')
        end_date = datetime.datetime.now().strftime('%Y-%m-%d')
        self.json_response = search_channel_listings(
            start_channel=2, end_channel=29,
            start_date=start_date, end_date=end_date)

    def test_update_db(self):
        upload_channel_search_response(self.json_response)
        self.assertGreater(
            Show.objects.count(),
            0
        )  # assert show was downloaded
        show = Show.objects.first()
        self.assertGreater(
            Episode.objects.filter(show=show).count(),
            0
        )  # ..and that it has at least 1 episode


class UpdateDownloadedRecordTests(TestCase):
    def setUp(self) -> None:
        Show.objects.create(
            id=1,
            title="Whose Line is it Anyway?",
            gid=79169
        )
        Episode.objects.create(
            show_id=1,
            title='Archie Hahn, Josie Lawrence, Paul Merton, John Sessions',
            downloaded=False,
        )

    def test_main(self):
        self.client.get(
            'http://localhost:8000/update_downloaded_record_for_episodes_in_show/1'
        )
        self.assertEqual(Episode.objects.first().downloaded, True)
