import os
import re
import webbrowser
from glob import glob
from bs4 import BeautifulSoup

import requests
from django.shortcuts import render, redirect
from .models import Show, Episode


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


class NZBGeek:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "https://github.com/kcinnick/nstv"})
        self.db_session = None
        self.logged_in = False

    def login(self):
        # get nzbgeek csrf token
        r = self.session.get("https://nzbgeek.info/logon.php")
        try:
            random_thing = re.search(
                r'<input type="hidden" name="random_thing" id="random_thing" value="(\w+)">',
                str(r.content),
            ).group(1)
        except AttributeError as e:
            #  occurs if user is already logged in
            if os.getenv('NZBGEEK_USERNAME') in str(r.content):
                return
            else:  # pragma: no cover
                print('Random thing for login was missing but user is not already logged in.')
                print('This should never happen. Something is wrong.  Look at the stacktrace:')
                print('\nHTML Content:', r.content)
                raise e
                #  until, (or if ever) the above occurs, we'll remove the noqa's above and test it accordingly.
                #  until then, unsure how to test it.
        # login to nzbgeek
        nzbgeek_login_url = "https://nzbgeek.info/logon.php"
        login_payload = {
            "logon": "logon",
            "random_thing": random_thing,
            "username": os.getenv("NZBGEEK_USERNAME"),
            "password": os.getenv("NZBGEEK_PASSWORD"),
        }
        self.session.post(nzbgeek_login_url, login_payload)
        r = self.session.get("https://nzbgeek.info/dashboard.php")
        assert os.getenv("NZBGEEK_USERNAME") in str(r.content)

    def get_nzb(
            self, show, season_number=None, episode_number=None, episode_title=None, hd=True
    ):
        """
        Searches and downloads the first result on NZBGeek for the given
        show and episode number. After the file is downloaded, it is moved
        to the directory specified in nzbget's Settings -> Path -> NzbDir
        for downloading and post-processing.
        @param show:  object representing the show the episode belongs to.
        @param season_number:  int
        @param episode_number:  int
        @param episode_title:  str, optional. If given, searches via show and episode title.
        @param hd:  bool, grabs only HD-categorized files if set to True
        @return:
        """
        print('sn:', season_number)
        if season_number and episode_number:
            print(f"\nSearching for {show.title} S{season_number} E{episode_number}")
            url = f"https://nzbgeek.info/geekseek.php?tvid={show.gid}"
            url += f"&season=S{str(season_number).zfill(2)}"
            url += f"&episode=E{str(episode_number).zfill(2)}"
        else:
            if not episode_title:
                raise AttributeError(
                    "get_nzb needs either season_number & episode_number"
                    " or an episode title."
                )
            url = "https://nzbgeek.info/geekseek.php?moviesgeekseek=1"
            url += "&c=5000&browseincludewords="
            url += f'{show.title.replace(" ", "+")}+'
            url += f'{episode_title.replace(" ", "+")}'

        print(f"\nRequesting {url}")
        r = self.session.get(url)

        soup = BeautifulSoup(r.content, "html.parser")
        results = soup.find_all("table", class_="releases")
        results = [SearchResult(i) for i in results]
        if hd:
            results = [i for i in results if i.category == "TV > HD"]

        if not len(results):
            print("No results found.")
            return
        webbrowser.open(results[0].download_url)
        #  TODO: above fails if no download links found
        from time import sleep

        #  wait until file is downloaded
        nzb_files = glob("/home/nick/Downloads/*.nzb")
        while len(nzb_files) == 0:
            sleep(1)
            nzb_files = glob("/home/nick/Downloads/*.nzb")
        print("\nNZB file downloaded.")

        for file in nzb_files:
            file_name = file.split("/")[-1]
            dest_path = f"/home/nick/PycharmProjects/nstv_fe/nzbs/{file_name}"
            os.rename(file, f"/home/nick/PycharmProjects/nstv_fe/nzbs/{file_name}")
            print(f"{file_name} moved to {dest_path}.")


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
