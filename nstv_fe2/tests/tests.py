import datetime
import os

from bs4 import BeautifulSoup
from django.test import TestCase

from nstv_fe2.models import Episode, Show
from nstv_fe2.nzbg import NZBGeek, SearchResult
from nstv_fe2.tvtv_scraper import search_channel_listings, upload_channel_search_response
from nstv_fe2.tests.shows.views.tests import ShowsIndexViewTests, ShowViewTests
from nstv_fe2.tests.shows.get_episode.tests import ShowTestCase
from nstv_fe2.tests.episodes.episode.tests import EpisodeTestCase
from nstv_fe2.tests.tvtvscraper.parse_channel_search_response.tests import TvtvScraperParseChannelSearchResponseTests
from nstv_fe2.tests.tvtvscraper.search_channels.tests import TvtvScraperSearchChannelsTests
from nstv_fe2.tests.tvtvscraper.update_db.tests import TvtvScraperUpdateDbTests
from nstv_fe2.tests.nzbgeek.tests import NZBGeekTests, DownloadEpisodeTests


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


class GetOutstandingSeasonEpisodeNumbersTests(TestCase):
    def setUp(self) -> None:
        Show.objects.create(
            id=1,
            title="Seinfeld",
            gid=79169
        )
        Episode.objects.create(
            id=1,
            title="The Parking Garage",
            original_air_date=datetime.date(1991, 10, 31),
            show=Show.objects.get(title="Seinfeld"),
        )

    def test_get_outstanding_season_episode_numbers(self):
        self.client.get(
            'http://localhost:8000/get_outstanding_season_episode_numbers'
        )
        self.assertEqual(Episode.objects.first().season, 3)
