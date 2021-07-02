import datetime

from django.test import TestCase

from nstv_fe2.tvtv_scraper import search_channel_listings, upload_channel_search_response


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