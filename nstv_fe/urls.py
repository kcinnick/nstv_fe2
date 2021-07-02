"""nstv_fe URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from nstv_fe2 import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.index, name="index"),
    path("index/", views.index, name="index"),
    path(
        "shows/<show_id>",
        views.show,
        name="show"
    ),
    path(
        "shows/<show_id>/season/<season_number>/episode/<episode_number>/nzbgeek",
        views.download_episode,
        name='nzbdownload'
    ),
    path(
        "shows/<show_id>/title/<episode_title>/nzbgeek",
        views.download_episode,
        name='nzbdownload',
    ),
    path(
        "update_database",
        views.search_and_update_show_and_episode_tables,
        name='update_database',
    ),
    path(
        "update_downloaded_record_for_episodes_in_show/<show_id>",
        views.update_downloaded_record_for_episodes_in_show,
        name='update_downloaded_records',
    ),
    path(
        "get_outstanding_season_episode_numbers",
        views.get_outstanding_season_episode_numbers,
        name='update_downloaded_records',
    )
]
