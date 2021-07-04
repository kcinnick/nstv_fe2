import datetime
import os

from bs4 import BeautifulSoup
from django.test import TestCase

from nstv_fe2.models import Episode, Show
from nstv_fe2.nzbg import NZBGeek, SearchResult
from nstv_fe2.tvtv_scraper import search_channel_listings, upload_channel_search_response


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