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
