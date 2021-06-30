import os

import plexapi.exceptions
from django.shortcuts import redirect, render
from plexapi.server import PlexServer

from .models import Episode, Show
from .nzbg import NZBGeek

#  TODO: add page for updating DB
from .tvtv_scraper import update_db


def update_downloaded_record_for_episodes_in_show(request, show_id):
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
        episode_model = Episode.objects.get(title=episode.title)
        episode_model.downloaded = True
        episode_model.save()

    return redirect(f'/shows/{show_id}')


def index(request):
    # update_db()
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
    #  TODO:
    update_db()

    return redirect("/")
