import datetime

import requests
from django.shortcuts import render, redirect

import nstv_fe2.models
from .models import Show, Episode
from .nzbg import NZBGeek


def index(request):
    shows = Show.objects.all()
    update_db()
    return render(request, context={"shows": shows}, template_name="index.html")


def show(request, show_id):
    show = Show.objects.get(id=show_id)
    show_episodes = Episode.objects.filter(show=show)
    return render(
        request,
        context={"show_episodes": show_episodes, "show": show},
        template_name="show.html",
    )


def download_episode(request, show_id, season_number=None, episode_number=None, episode_title=None):
    nzb_geek = NZBGeek()
    nzb_geek.login()
    if episode_title:
        episode = Episode.objects.get(title=episode_title)
    else:
        episode = Episode.objects.get(season=season_number, number=episode_number)

    parent_show = Show.objects.get(id=show_id)
    if episode_title:
        print('Episode title: {}'.format(episode_title))
    else:
        print('Episode title: {}'.format(episode.title))

    if episode_title:
        nzb_geek.get_nzb(
            show=parent_show,
            episode_title=episode_title,
        )
    else:
        nzb_geek.get_nzb(
            show=parent_show,
            episode_title=episode.title,
        )

    return redirect(f'/shows/{show_id}')


def get_or_create_show(listing, title=None):
    #  TODO: this shouldn't be in views.
    """
    listing:  JSON object representing an episode listing returned by nstv.search_channels
    db_session:  sqlalchemy.orm.Session object

    Creates and returns new Show object for show indicated in an
    episode listing and commits the object against the database.
    If an object matching the show's title already exists,
    this function only returns the existing show's object.
    """
    #  check if show exists in DB
    used_ids = [int(i) for i in Show.objects.values_list('id', flat=True)]

    if title:
        listing['showName'] = title

    usable_ids = [i for i in range(1000) if i not in used_ids]

    try:
        show = Show.objects.get(title=listing['showName'])
        print(f"{listing['showName']} already in DB.")
    except nstv_fe2.models.Show.DoesNotExist:
        # create new Show
        show = Show.objects.create(
            title=listing['showName'],
            id=usable_ids[0]
        )
        print(f"{listing['showName']} added to DB.")

    return show


def search_channels(start_channel, end_channel, start_date, end_date):
    #  TODO: this shouldn't be in views.
    """
    start_channel: int
    end_channel: int

    Executes a search for the supplied range of channels from start_channel
    to end_channel and returns the accompanying JSON response object.
    """
    if start_channel > end_channel:
        print('The search has a start channel that\'s higher than the end_channel.')
        print('This doesn\'t make sense.  Check your inputs.')
        print(f'Start channel: {start_channel}')
        print(f'End channel: {end_channel}')
        raise ValueError()

    print('\nSearching channels for TV showing details..\n')
    url = f'https://tvtv.us/tvm/t/tv/v4/lineups/95197D/listings/grid?detail='
    url += '%27brief%27&'
    url += f'start={start_date}T04:00:00.000'
    url += 'Z&'
    url += f'end={end_date}T03:59:00.000'
    url += f'Z&startchan={start_channel}&endchan={end_channel}'
    r = requests.get(
        url
    )
    assert r.status_code == 200
    return r.json()


def get_or_create_episode(listing, show):
    """
    listing:  JSON object representing an episode listing returned by nstv.search_channels
    db_session:  sqlalchemy.orm.Session object

    Creates and returns new Episode object for episode indicated in a
    listing and commits the object against the database.
    If an object matching the episode's title already exists,
    this function only returns the existing episode's object.
    """
    used_ids = [int(i) for i in Episode.objects.values_list('id', flat=True)]

    usable_ids = [i for i in range(1000) if i not in used_ids]

    try:
        episode = Episode.objects.get(title=listing['episodeTitle'])
    except Episode.DoesNotExist:
        episode = Episode.objects.create(
            id=usable_ids[0],
            title=listing['episodeTitle'],
            original_air_date=listing['listDateTime'].replace('“', '').replace('”', '').split()[0],
            show=show,
        )

    return episode


def parse_channel_search_response(response):
    #  TODO: this shouldn't be in views
    """
    db_session:  sqlalchemy.orm.Session object
    response:  JSON object containing a list of episodes returned by a call to search_channels

    Parses the JSON response returned from a search
    into the appropriate episode or show models.
    """
    for i in response:
        print('~~~')
        listings = i['listings']
        shows = []
        episodes = []
        for listing in listings:
            if listing['showName'] == 'Paid Program':
                continue
            show = get_or_create_show(listing)
            if show not in shows:
                shows.append(show)
            episode = get_or_create_episode(listing, show)
            if episode not in episodes:
                episodes.append(episode)


def update_db():
    start_date = (datetime.datetime.now() - datetime.timedelta(10)).strftime('%Y-%m-%d')
    end_date = datetime.datetime.now().strftime('%Y-%m-%d')

    json_response = search_channels(
        start_channel=44, end_channel=47,
        start_date=start_date, end_date=end_date)
    parse_channel_search_response(json_response)
