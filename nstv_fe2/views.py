import requests
from django.shortcuts import render, redirect

from .models import Show, Episode
from .nzbg import NZBGeek


def index(request):
    shows = Show.objects.all()
    return render(request, context={"shows": shows}, template_name="index.html")


def show(request, show_id):
    show = Show.objects.get(id=show_id)
    show_episodes = Episode.objects.filter(show=show)
    return render(
        request,
        context={"show_episodes": show_episodes, "show": show},
        template_name="show.html",
    )


def download_episode(request, show_id, season_number, episode_number):
    nzb_geek = NZBGeek()
    nzb_geek.login()
    episode = Episode.objects.get(season=season_number, number=episode_number)
    parent_show = Show.objects.get(id=show_id)
    print('Episode title: {}'.format(episode.title))
    nzb_geek.get_nzb(
        show=parent_show,
        episode_title=episode.title,
    )
    return redirect(f'/shows/{show_id}')


def search_channels(start_channel, end_channel, start_date, end_date):
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
