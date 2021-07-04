import datetime
import os

from bs4 import BeautifulSoup
from django.test import TestCase

from nstv_fe2.models import Episode, Show
from nstv_fe2.nzbg import NZBGeek, SearchResult
from nstv_fe2.tvtv_scraper import search_channel_listings, upload_channel_search_response


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
