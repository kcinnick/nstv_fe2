import datetime

import requests

from .models import Episode, Show


def search_channels(start_channel, end_channel, start_date, end_date):
    """
    start_channel: int
    end_channel: int

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
    url += f"start={start_date}T04:00:00.000"
    url += "Z&"
    url += f"end={end_date}T03:59:00.000"
    url += f"Z&startchan={start_channel}&endchan={end_channel}"
    r = requests.get(url)
    assert r.status_code == 200
    return r.json()


def parse_channel_search_response(response):
    """
    db_session:  sqlalchemy.orm.Session object
    response:  JSON object containing a list of episodes returned by a call to search_channels

    Parses the JSON response returned from a search
    into the appropriate episode or show models.
    """
    for i in response:  # TODO: use a real variable name
        #  TODO:  write test
        print("~~~")
        listings = i["listings"]
        shows = []
        episodes = []
        for listing in listings:
            if listing["showName"] == "Paid Program":
                continue
            show = get_or_create_show(listing)
            if show not in shows:
                shows.append(show)
            episode = get_or_create_episode(listing, show)
            if episode not in episodes:
                episodes.append(episode)


def update_db():
    #  TODO:  write test
    start_date = (datetime.datetime.now() - datetime.timedelta(10)).strftime("%Y-%m-%d")
    end_date = datetime.datetime.now().strftime("%Y-%m-%d")

    #  TODO: make channels variable, run this through a util
    json_response = search_channels(
        start_channel=45,
        end_channel=47,
        start_date=start_date,
        end_date=end_date
    )
    parse_channel_search_response(json_response)


def get_or_create_show(listing, title=None):
    """
    listing:  JSON object representing an episode listing returned by nstv.search_channels

    Creates and returns new Show object for show indicated in an
    episode listing and commits the object against the database.
    If an object matching the show's title already exists,
    this function only returns the existing show's object.
    """
    #  check if show exists in DB
    #  TODO:  write test
    if title:
        listing["showName"] = title

    try:
        show = Show.objects.get(title=listing["showName"])
        print(f"{listing['showName']} already in DB.")
    except Show.DoesNotExist:
        # create new Show
        show = Show.objects.create(title=listing["showName"])
        print(f"{listing['showName']} added to DB.")

    return show


def get_or_create_episode(listing, show):
    """
    listing:  JSON object representing an episode listing returned by nstv.search_channels

    Creates and returns new Episode object for episode indicated in a
    listing and commits the object against the database.
    If an object matching the episode's title already exists,
    this function only returns the existing episode's object.
    """
    #  TODO:  write test
    try:
        episode = Episode.objects.get(title=listing["episodeTitle"])
    except Episode.DoesNotExist:
        episode = Episode.objects.create(
            title=listing["episodeTitle"],
            original_air_date=listing["listDateTime"]
                .replace("“", "")
                .replace("”", "")
                .split()[0],
            show=show,
        )

    return episode
