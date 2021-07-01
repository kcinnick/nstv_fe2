import os
import re
import webbrowser
from glob import glob
from time import sleep

import requests
from bs4 import BeautifulSoup


class SearchResult:
    """
    A programmatic representation of the search result listings returned by
    NZBGeek's web interface.  Unsure if it's really needed, should TODO some
    cleanup on it at some point.
    """

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
        """
        Checks if user is already logged, and if not, attempts a login.
        :return:
        """
        # get nzbgeek csrf token
        if self.logged_in:
            print("User already logged in.\n")
            return

        nzbgeek_login_url = "https://nzbgeek.info/logon.php"
        r = self.session.get(nzbgeek_login_url)

        random_thing = re.search(
            r'<input type="hidden" name="random_thing" id="random_thing" value="(\w+)">',
            str(r.content),
        ).group(1)
        login_payload = {
            "logon": "logon",
            "random_thing": random_thing,
            "username": os.getenv("NZBGEEK_USERNAME"),
            "password": os.getenv("NZBGEEK_PASSWORD"),
        }
        self.session.post(nzbgeek_login_url, login_payload)
        r = self.session.get("https://nzbgeek.info/dashboard.php")

        assert os.getenv("NZBGEEK_USERNAME") in str(r.content)
        self.logged_in = True

        return

    def _build_search_url(
            self, show, season_number, episode_number, episode_title=None
    ):
        """
        Builds a valid search URL depending on whether or not the episode is being
        searched by a season/episode number or episode title.
        :param show: .models.Show object
        :param season_number: int, the season the episode belongs to
        :param episode_number: int, the episode's number
        :param episode_title: str, the episode's title
        :return:
        """
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
            print(f"\nSearching for {show.title} - {episode_title}")
            url = "https://nzbgeek.info/geekseek.php?moviesgeekseek=1"
            url += "&c=5000&browseincludewords="
            url += f'{show.title.replace(" ", "+")}+'
            url += f'{episode_title.replace(" ", "+")}'

        return url

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
        url = self._build_search_url(
            show=show,
            episode_number=episode_number,
            season_number=season_number,
            episode_title=episode_title,
        )
        print(f"\nRequesting {url}")
        r = self.session.get(url)

        soup = BeautifulSoup(r.content, "html.parser")
        results = soup.find_all("table", class_="releases")
        results = [SearchResult(i) for i in results]
        if hd:
            results = [i for i in results if i.category == "TV > HD"]

        if not len(results):
            raise ValueError("No results found.")  # TODO: this should be more delicately handled

        webbrowser.open(results[0].download_url)

        #  wait until file is downloaded
        nzb_files = glob("/home/nick/Downloads/*.nzb")
        while len(nzb_files) == 0:  # pragma: no cover
            sleep(1)
            nzb_files = glob("/home/nick/Downloads/*.nzb")
        print("\nNZB file downloaded.")

        for file in nzb_files:
            #  rename and move the files from Downloads to nstv_fe/nzbs/*
            file_name = file.split("/")[-1]
            dest_path = f"/home/nick/PycharmProjects/nstv_fe/nzbs/{file_name}"
            os.rename(file, f"/home/nick/PycharmProjects/nstv_fe/nstv_fe2/finished/{file_name}")
            print(f"{file_name} moved to {dest_path}.")

        return
