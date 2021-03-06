import datetime

import requests
from django.db import IntegrityError

from .models import Episode, Show


def search_channel_listings(start_channel, end_channel, start_date, end_date):
    """
    :param start_channel: int
    :param end_channel: int
    :param start_date: str, YYYY-MM-DD format
    :param end_date: str, YYYY-MM-DD format

    Executes a search for the supplied range of channels from start_channel
    to end_channel and returns the accompanying JSON response object.
    """
    if start_channel > end_channel:
        msg = "The search has a start channel that's higher than the end_channel."
        msg += "\nThis doesn't make sense.  Check your inputs."
        msg += f"\nStart channel: {start_channel}"
        msg += f"\nEnd channel: {end_channel}"
        raise ValueError(msg)

    print("\nSearching channels for TV showing details..\n")
    url = f"https://tvtv.us/tvm/t/tv/v4/lineups/95197D/listings/grid?detail="
    url += "%27brief%27&"
    url += f"start={start_date}T00:00:00.000"
    url += "Z&"
    url += f"end={end_date}T23:59:00.000"
    url += f"Z&startchan={start_channel}&endchan={end_channel}"
    r = requests.get(url)
    assert r.status_code == 200
    return r.json()


def upload_channel_search_response(response):
    """
    :param response:  dict, representation of JSON object containing a list of episodes returned by a call to search_channels

    Parses the JSON response returned from a search into the appropriate episode or show models.
    """
    for channel_listing_response in response:
        listings = channel_listing_response["listings"]
        for listing in listings:
            if listing["showName"] == "Paid Program":
                continue
            show = Show.objects.get_or_create(title=listing["showName"])[0]
            if len(listing["episodeTitle"].strip()):
                title = listing["episodeTitle"]
            else:
                title = listing["episodeNumber"]
            try:
                Episode.objects.get_or_create(
                    title=title,
                    show_id=show.id,
                    season=listing["seasonNumber"],
                    number=listing["seasonSeqNo"],
                )
            except IntegrityError:
                continue
                #  TODO: handle these more properly.
                #  they occur a lot on local news programs.
