import os
import imdb
import plexapi.exceptions
from django.shortcuts import redirect, render
from plexapi.server import PlexServer

from .models import Episode, Show
from .nzbg import NZBGeek

#  TODO: add page for updating DB
from .tvtv_scraper import main as run_tvtv_scraper


def update_downloaded_record_for_episodes_in_show(request, show_id):
    """

    :param request:
    :param show_id: ID of .models.Show object to update
    :return:
    """
    django_show_title = Show.objects.get(id=show_id).title
    base_url = 'http://localhost:32400'
    token = os.getenv('PLEX_TOKEN')
    try:
        plex = PlexServer(base_url, token)
    except plexapi.exceptions.Unauthorized:
        raise PermissionError(
            '401 unauthorized for Plex. Did you set the PLEX_TOKEN environment variable (and is it valid)?'
        )
    plex_show = plex.library.section('TV Shows').get(django_show_title)
    for episode in plex_show.episodes():
        season = episode.parentTitle.split()[-1]
        number = episode.index
        try:
            episode_model = Episode.objects.get(title=episode.title)
        except Episode.DoesNotExist:
            episode_model = Episode.objects.create(
                title=episode.title,
            )
        episode_model.downloaded = True
        episode_model.season = season
        episode_model.number = number
        episode_model.save()

    return redirect(f'/shows/{show_id}?updated=True')


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


def download_episode(
        request, show_id, season_number=None, episode_number=None, episode_title=None
):
    nzb_geek = NZBGeek()
    nzb_geek.login()
    if not episode_title:
        episode = Episode.objects.get(season=season_number, number=episode_number)
        episode_title = episode.title

    parent_show = Show.objects.get(id=show_id)
    print("Episode title: {}".format(episode_title))
    nzb_geek.get_nzb(show=parent_show, episode_title=episode_title)

    return redirect(f"/shows/{show_id}")


def search_and_update_show_and_episode_tables(
        request
):
    #  TODO: seems wrong to have a function just for one line of code
    run_tvtv_scraper()
    return redirect("/")


def get_outstanding_season_episode_numbers(
        request
):
    ia = imdb.IMDb()
    episodes_without_season_episode_numbers = Episode.objects.filter(season=None)
    print(f'{episodes_without_season_episode_numbers.count()} episodes found.')
    for episode in episodes_without_season_episode_numbers:
        print('~~~')
        print(f'Searching for {episode.title}')
        try:
            results = ia.search_episode(episode.title)
        except imdb._exceptions.IMDbParserError:
            continue  # happens if Show entry doesn't have a title
        try:
            first_result_for_show = [i for i in results if i['episode of'].lower() == episode.show.title.lower()][0]
        except IndexError:
            continue
        except AttributeError:
            continue
        try:
            episode.season = first_result_for_show['season']
            episode.number = first_result_for_show['episode']
        except KeyError:
            continue
        episode.save()
        print(f'Episode {episode.title} of {episode.show.title} season/episode number updated.')

    return redirect("/")
