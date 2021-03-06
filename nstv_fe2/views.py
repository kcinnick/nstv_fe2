import datetime
import os
import shutil

import imdb
import plexapi.exceptions
from django.shortcuts import redirect, render
from plexapi.server import PlexServer

from .models import Episode, Show
from .nzbg import NZBGeek

from .tvtv_scraper import upload_channel_search_response, search_channel_listings


def refresh_plex_section(section_name='TV Shows'):
    """
    After moving a downloaded TV show to the external hard drive, it
    won't show up in Plex unless we refresh the Plex section it belongs to.
    :param section_name:
    :return:
    """
    #  TODO: write logic to ping '/library/sections/section ID/refresh'
    base_url = "http://localhost:32400"
    token = os.getenv("PLEX_TOKEN")
    try:
        plex = PlexServer(base_url, token)
    except plexapi.exceptions.Unauthorized as e:
        #  if you need to get a new PLEX_TOKEN, follow the instructions here:
        #  https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/
        print(
            "401 unauthorized for Plex. Did you set the PLEX_TOKEN environment variable (and is it valid)?"
        )
        raise e

    section = plex.library.section(section_name)
    section.update()
    return


def move_downloaded_files_to_path(nzb_dest_dir, plex_dest_dir):
    """
    Files will be downloaded to the path specified in NZBGet -> Settings -> Paths -> DestDir.
    From there, we need to add them to the path that Plex looks at to find new files.
    :param nzb_dest_dir: str, path specified in NZBGet -> Settings -> Paths -> DestDir
    :param plex_dest_dir: str, path specified in the Add Folders section on the /manage/libraries Plex page.
    :return:
    """
    for file in os.listdir(nzb_dest_dir):
        #  this will fail unless the user trying to move the files `owns` them.
        #  ex:  sudo chown <user> -R * in nzb_dest_dir
        shutil.move(f'{nzb_dest_dir}/{file}', plex_dest_dir)
    return


def update_downloaded_record_for_episodes_in_show(request, show_id):
    """
    Checks Plex for episodes that are currently on disk, and iterates over
    the corresponding Episode objects in the nstv_fe database and updates
    the season/episode number if necessary.

    :param request: django.http.request
    :param show_id: ID of .models.Show object to update
    :return:
    """
    django_show_title = Show.objects.get(id=show_id).title
    base_url = "http://localhost:32400"
    token = os.getenv("PLEX_TOKEN")
    try:
        plex = PlexServer(base_url, token)
    except plexapi.exceptions.Unauthorized as e:
        #  if you need to get a new PLEX_TOKEN, follow the instructions here:
        #  https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/
        print(
            "401 unauthorized for Plex. Did you set the PLEX_TOKEN environment variable (and is it valid)?"
        )
        raise e
    try:
        plex_show = plex.library.section("TV Shows").get(django_show_title)
    except plexapi.exceptions.NotFound as e:
        #  some shows exist in the Django database, but don't exist in the Plex library.
        #  this is because 0 episodes of that show have been downloaded, so there's no
        #  record of the show in Plex.
        raise e

    for episode in plex_show.episodes():
        season = episode.parentTitle.split()[-1]
        number = episode.index
        try:
            episode_model = Episode.objects.get(title=episode.title)
        except Episode.DoesNotExist:
            #  if a show exists on the hard drive but not in the nstv_fe database,
            #  we'll create it and mark it as downloaded.
            episode_model = Episode.objects.create(title=episode.title)
        episode_model.downloaded = True
        episode_model.season = season
        episode_model.number = number
        episode_model.save()

    return redirect(f"/shows/{show_id}?updated=True")


def index(request):
    """
    Returns an index of the shows in the database.
    :param request: django.http.request
    :return:
    """
    shows = Show.objects.all()
    return render(request, context={"shows": shows}, template_name="index.html")


def show(request, show_id):
    """
    Index of episodes for the Show model with the pk of the given show_id.
    :param request: django.http.request
    :param show_id: int
    :return:
    """
    show = Show.objects.get(id=show_id)
    show_episodes = Episode.objects.filter(show=show).order_by("season", "number")
    return render(
        request,
        context={"show_episodes": show_episodes, "show": show},
        template_name="show.html",
    )


def download_episode(
        request, show_id, season_number=None, episode_number=None, episode_title=None
):
    """
    Downloads an episode of the Show (identified by ID of the show in the database)
    and an episode title or the season & episode number. Redirects back to the show's
    page after the download.

    :param request: django.http.request
    :param show_id: int, ID of the associated Show model
    :param season_number: int, season number of the episode to download
    :param episode_number: int, episode_number of the episode to download
    :param episode_title: str, title of the episode to download
    :return:
    """
    nzb_geek = NZBGeek()
    nzb_geek.login()
    if not episode_title:
        episode = Episode.objects.get(season=season_number, number=episode_number)
        episode_title = episode.title

    parent_show = Show.objects.get(id=show_id)
    print(f"Episode title: {episode_title}")
    downloaded = nzb_geek.get_nzb(show=parent_show, episode_title=episode_title)
    if downloaded:
        print(f"Episode {episode_title} for {parent_show.title} downloaded.")
    else:
        print(f"Couldn't locate episode {episode_title} for {parent_show.title}")
        if not season_number:
            print("Search was committed via episode title.")
    return redirect(f"/shows/{show_id}")


def search_and_update_show_and_episode_tables(request, start_date=None, end_date=None):
    """

    :param request: django.http.request
    :param start_date: str, date represented as YYYY-MM-DD
    :param end_date: str, date represented as YYYY-MM-DD
    :return:
    """
    if not start_date:
        start_date = (datetime.datetime.now() - datetime.timedelta(2)).strftime(
            "%Y-%m-%d"
        )
        end_date = datetime.datetime.now().strftime("%Y-%m-%d")

    json_response = search_channel_listings(
        start_channel=45, end_channel=47, start_date=start_date, end_date=end_date
    )
    upload_channel_search_response(json_response)
    return redirect("/")


def get_outstanding_season_episode_numbers(request):
    """
    For each Episode object in every Show in the database without one,
    attempts to get a season and episode number for each for later downloading.

    :param request: django.http.request
    :return:
    """
    ia = imdb.IMDb()
    episodes_without_season_episode_numbers = Episode.objects.filter(season=None)
    print(
        f"{episodes_without_season_episode_numbers.count()} episodes without season or episode numbers found."
    )
    print("Attempting to update.")
    for episode in episodes_without_season_episode_numbers:
        print("~~~")
        print(f"Searching for {episode.title}")
        try:
            results = ia.search_episode(episode.title)
        except imdb._exceptions.IMDbParserError:
            continue  # happens if episode entry doesn't have a title
        try:
            first_result_for_show = [
                i
                for i in results
                if i["episode of"].lower() == episode.show.title.lower()
            ][0]
        except IndexError:
            continue  # happens if episode can't be found in IMDB
        except AttributeError:
            continue  # happens if episode belongs to a show without a title

        episode.season = first_result_for_show.get("season")
        episode.number = first_result_for_show.get("episode")

        episode.save()
        print(
            f"Episode {episode.title} of {episode.show.title} season/episode number updated."
        )

    return redirect("/")
