from django.shortcuts import render, redirect

from .models import Show, Episode
from .nzbg import NZBGeek


class SearchResult:
    def __init__(self, result_table):
        self.title = result_table.find("a", class_="releases_title").text.strip()
        self.category = result_table.find(
            "a", class_="releases_category_text"
        ).text.strip()
        self.file_size = result_table.find("td", class_="releases_size").text.strip()
        self.download_url = result_table.find("a", attrs={"title": "Download NZB"}).get(
            "href"
        )

    def __str__(self):
        return f"{self.title}, {self.category}"


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
    print(
        f"\nseason number: {season_number}"
        f"\nepisode_number: {episode_number}"
        f"\nshow ID: {show_id}"
    )

    nzb_geek = NZBGeek()
    nzb_geek.login()
    episode = Episode.objects.get(season=season_number, number=episode_number)
    parent_show = Show.objects.get(id=show_id)
    print('Episode title: {}'.format(episode.title))
    if episode.title:
        nzb_geek.get_nzb(
            show=parent_show,
            episode_title=episode.title,
        )
    else:
        print(
            'Searching shows by season or episode number '
            'isn\'t currently supported.\n'
        )
        raise NotImplementedError

    return redirect(f'/shows/{show_id}')
