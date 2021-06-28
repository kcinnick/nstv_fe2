import os

from django.shortcuts import redirect, render
from plexapi.server import PlexServer

from .models import Episode, Show
from .nzbg import NZBGeek

#  TODO: add page for updating DB
from .tvtv_scraper import update_db


def get_seinfeld_episodes():
    baseurl = 'http://localhost:32400'
    token = os.getenv('PLEX_TOKEN')
    plex = PlexServer(baseurl, token)
    seinfeld = plex.library.section('TV Shows').get('Seinfeld')
    for episode in seinfeld.episodes():
        try:
            episode_model = Episode.objects.get(title=episode.title)
        except Episode.DoesNotExist:
            episode_model = Episode.objects.create(
                    title=episode.title,
                )
            episode_model.downloaded = False
        else:
            episode_model.downloaded = True
        episode_model.save()


def index(request):
    update_db()
    shows = Show.objects.all()
    get_seinfeld_episodes()
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
