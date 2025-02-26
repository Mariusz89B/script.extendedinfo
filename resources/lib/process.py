# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details



import time
import os
import shutil

import xbmc
import xbmcgui
import xbmcplugin

from resources.lib import Trakt
from resources.lib import LastFM
from resources.lib import TheAudioDB as AudioDB
from resources.lib import TheMovieDB as tmdb
from .WindowManager import wm

from kodi65 import youtube
from kodi65 import local_db
from kodi65 import addon
from kodi65 import utils
from kodi65 import busy
from kodi65 import kodijson
from kodi65 import favs


def start_info_actions(info, params):
    if "artistname" in params:
        params["artistname"] = params.get("artistname", "").split(" feat. ")[0].strip()
        if not params.get("artist_mbid"):
            params["artist_mbid"] = utils.fetch_musicbrainz_id(params["artistname"])
    utils.log(info)
    utils.pp(params)
    if "prefix" in params and not params["prefix"].endswith('.'):
        params["prefix"] = params["prefix"] + '.'

    # Audio
    if info == 'discography':
        discography = AudioDB.get_artist_discography(params["artistname"])
        if not discography:
            discography = LastFM.get_artist_albums(params.get("artist_mbid"))
        return discography
    elif info == 'mostlovedtracks':
        return AudioDB.get_most_loved_tracks(params["artistname"])
    elif info == 'trackdetails':
        return AudioDB.get_track_details(params.get("id", ""))
    elif info == 'topartists':
        return LastFM.get_top_artists()
    #  The MovieDB
    elif info == 'incinemamovies':
        return tmdb.get_movies("now_playing")
    elif info == 'upcomingmovies':
        return tmdb.get_movies("upcoming")
    elif info == 'topratedmovies':
        return tmdb.get_movies("top_rated")
    elif info == 'popularmovies':
        return tmdb.get_movies("popular")
    elif info == 'ratedmovies':
        return tmdb.get_rated_media_items("movies")
    elif info == 'starredmovies':
        return tmdb.get_fav_items("movies")
    elif info == 'accountlists':
        account_lists = tmdb.handle_lists(tmdb.get_account_lists())
        for item in account_lists:
            item.set_property("directory", True)
        return account_lists
    elif info == 'listmovies':
        return tmdb.get_movies_from_list(params["id"])
    elif info == 'airingtodaytvshows':
        return tmdb.get_tvshows("airing_today")
    elif info == 'onairtvshows':
        return tmdb.get_tvshows("on_the_air")
    elif info == 'topratedtvshows':
        return tmdb.get_tvshows("top_rated")
    elif info == 'populartvshows':
        return tmdb.get_tvshows("popular")
    elif info == 'ratedtvshows':
        return tmdb.get_rated_media_items("tv")
    elif info == 'ratedepisodes':
        return tmdb.get_rated_media_items("tv/episodes")
    elif info == 'starredtvshows':
        return tmdb.get_fav_items("tv")
    elif info == 'similarmovies':
        movie_id = params.get("id")
        if not movie_id:
            movie_id = tmdb.get_movie_tmdb_id(imdb_id=params.get("imdb_id"),
                                              dbid=params.get("dbid"))
        if movie_id:
            return tmdb.get_similar_movies(movie_id)
    elif info == 'similartvshows':
        tvshow_id = None
        dbid = params.get("dbid")
        name = params.get("name")
        tmdb_id = params.get("tmdb_id")
        tvdb_id = params.get("tvdb_id")
        imdb_id = params.get("imdb_id")
        if tmdb_id:
            tvshow_id = tmdb_id
        elif dbid and int(dbid) > 0:
            tvdb_id = local_db.get_imdb_id("tvshow", dbid)
            if tvdb_id:
                tvshow_id = tmdb.get_show_tmdb_id(tvdb_id)
        elif tvdb_id:
            tvshow_id = tmdb.get_show_tmdb_id(tvdb_id)
        elif imdb_id:
            tvshow_id = tmdb.get_show_tmdb_id(imdb_id, "imdb_id")
        elif name:
            tvshow_id = tmdb.search_media(media_name=name,
                                          year="",
                                          media_type="tv")
        if tvshow_id:
            return tmdb.get_similar_tvshows(tvshow_id)
    elif info == 'studio':
        if params.get("id"):
            return tmdb.get_company_data(params["id"])
        elif params.get("studio"):
            company_data = tmdb.search_companies(params["studio"])
            if company_data:
                return tmdb.get_company_data(company_data[0]["id"])
    elif info == 'set':
        if params.get("dbid"):
            name = local_db.get_set_name(params["dbid"])
            if name:
                params["setid"] = tmdb.get_set_id(name)
        if params.get("setid"):
            set_data, _ = tmdb.get_set_movies(params["setid"])
            return set_data
    elif info == 'movielists':
        movie_id = params.get("id")
        if not movie_id:
            movie_id = tmdb.get_movie_tmdb_id(imdb_id=params.get("imdb_id"),
                                              dbid=params.get("dbid"))
        if movie_id:
            return tmdb.get_movie_lists(movie_id)
    elif info == 'keywords':
        movie_id = params.get("id")
        if not movie_id:
            movie_id = tmdb.get_movie_tmdb_id(imdb_id=params.get("imdb_id"),
                                              dbid=params.get("dbid"))
        if movie_id:
            return tmdb.get_keywords(movie_id)
    elif info == 'trailers':
        movie_id = params.get("id")
        if not movie_id:
            movie_id = tmdb.get_movie_tmdb_id(imdb_id=params.get("imdb_id"),
                                              dbid=params.get("dbid"))
        if movie_id:
            return tmdb.handle_videos(tmdb.get_movie_videos(movie_id))
    elif info == 'popularpeople':
        return tmdb.get_popular_actors()
    elif info == 'personmovies':
        person = tmdb.get_person_info(person_label=params.get("person"),
                                      skip_dialog=True)
        if person and person.get("id"):
            movies = tmdb.get_person_movies(person["id"])
            if not movies:
                return None
            for item in movies:
                del item["credit_id"]
            return movies.reduce(key="department")
    elif info == 'traktsimilarmovies':
        if params.get("id") or params.get("dbid"):
            if params.get("dbid"):
                movie_id = local_db.get_imdb_id("movie", params["dbid"])
            else:
                movie_id = params["id"]
            return Trakt.get_similar("movie", movie_id)
    elif info == 'traktsimilartvshows':
        if params.get("id") or params.get("dbid"):
            if params.get("dbid"):
                if params.get("type") == "episode":
                    tvshow_id = local_db.get_tvshow_id_by_episode(params["dbid"])
                else:
                    tvshow_id = local_db.get_imdb_id(media_type="tvshow",
                                                     dbid=params["dbid"])
            else:
                tvshow_id = params["id"]
            return Trakt.get_similar("show", tvshow_id)
    elif info == 'airingepisodes':
        return Trakt.get_episodes("shows")
    elif info == 'premiereepisodes':
        return Trakt.get_episodes("premieres")
    elif info == 'trendingshows':
        return Trakt.get_shows("trending")
    elif info == 'popularshows':
        return Trakt.get_shows("popular")
    elif info == 'anticipatedshows':
        return Trakt.get_shows("anticipated")
    elif info == 'mostcollectedshows':
        return Trakt.get_shows_from_time("collected")
    elif info == 'mostplayedshows':
        return Trakt.get_shows_from_time("played")
    elif info == 'mostwatchedshows':
        return Trakt.get_shows_from_time("watched")
    elif info == 'trendingmovies':
        return Trakt.get_movies("trending")
    elif info == 'traktpopularmovies':
        return Trakt.get_movies("popular")
    elif info == 'mostplayedmovies':
        return Trakt.get_movies_from_time("played")
    elif info == 'mostwatchedmovies':
        return Trakt.get_movies_from_time("watched")
    elif info == 'mostcollectedmovies':
        return Trakt.get_movies_from_time("collected")
    elif info == 'mostanticipatedmovies':
        return Trakt.get_movies("anticipated")
    elif info == 'traktboxofficemovies':
        return Trakt.get_movies("boxoffice")
    elif info == 'similarartistsinlibrary':
        return local_db.get_similar_artists(params.get("artist_mbid"))
    elif info == 'trackinfo':
        addon.clear_global('%sSummary' % params.get("prefix", ""))
        if params["artistname"] and params["trackname"]:
            track_info = LastFM.get_track_info(artist_name=params["artistname"],
                                               track=params["trackname"])
            addon.set_global('%sSummary' % params.get("prefix", ""), track_info["summary"])
    elif info == 'topartistsnearevents':
        artists = local_db.get_artists()
        from . import BandsInTown
        return BandsInTown.get_near_events(artists[0:49])
    elif info == 'youtubesearchvideos':
        addon.set_global('%sSearchValue' % params.get("prefix", ""), params.get("id", ""))
        if params.get("id"):
            return youtube.search(search_str=params.get("id", ""),
                                  hd=params.get("hd"),
                                  orderby=params.get("orderby", "relevance"))
    elif info == 'youtubeplaylistvideos':
        return youtube.get_playlist_videos(params.get("id", ""))
    elif info == 'youtubeusersearchvideos':
        user_name = params.get("id")
        if user_name:
            playlists = youtube.get_user_playlists(user_name)
            return youtube.get_playlist_videos(playlists["uploads"])
    elif info == 'favourites':
        if params.get("id"):
            items = favs.get_favs_by_type(params["id"])
        else:
            items = favs.get_favs()
            addon.set_global('favourite.count', str(len(items)))
            if items:
                addon.set_global('favourite.1.name', items[-1]["label"])
        return items
    elif info == "addonsbyauthor":
        items = favs.get_addons_by_author(params.get("id"))
    elif info == 'similarlocalmovies' and "dbid" in params:
        return local_db.get_similar_movies(params["dbid"])
    elif info == 'iconpanel':
        return favs.get_icon_panel(int(params["id"])), "IconPanel" + str(params["id"])
    # ACTIONS
    if params.get("handle"):
        xbmcplugin.setResolvedUrl(handle=int(params.get("handle")),
                                  succeeded=False,
                                  listitem=xbmcgui.ListItem())
    if info in ['playmovie', 'playepisode', 'playmusicvideo', 'playalbum', 'playsong']:
        kodijson.play_media(media_type=info.replace("play", ""),
                            dbid=params.get("dbid"),
                            resume=params.get("resume", "true"))
    elif info == "openinfodialog":
        if xbmc.getCondVisibility("System.HasActiveModalDialog"):
            container_id = ""
        else:
            container_id = "Container(%s)" % utils.get_infolabel("System.CurrentControlId")
        dbid = utils.get_infolabel("%sListItem.DBID" % container_id)
        db_type = utils.get_infolabel("%sListItem.DBType" % container_id)
        if db_type == "movie":
            params = {"dbid": dbid,
                      "id": utils.get_infolabel("%sListItem.Property(id)" % container_id),
                      "name": utils.get_infolabel("%sListItem.Title" % container_id)}
            start_info_actions("extendedinfo", params)
        elif db_type == "tvshow":
            params = {"dbid": dbid,
                      "tvdb_id": utils.get_infolabel("%sListItem.Property(tvdb_id)" % container_id),
                      "id": utils.get_infolabel("%sListItem.Property(id)" % container_id),
                      "name": utils.get_infolabel("%sListItem.Title" % container_id)}
            start_info_actions("extendedtvinfo", params)
        elif db_type == "season":
            params = {"tvshow": utils.get_infolabel("%sListItem.TVShowTitle" % container_id),
                      "season": utils.get_infolabel("%sListItem.Season" % container_id)}
            start_info_actions("seasoninfo", params)
        elif db_type == "episode":
            params = {"tvshow": utils.get_infolabel("%sListItem.TVShowTitle" % container_id),
                      "season": utils.get_infolabel("%sListItem.Season" % container_id),
                      "episode": utils.get_infolabel("%sListItem.Episode" % container_id)}
            start_info_actions("extendedepisodeinfo", params)
        elif db_type in ["actor", "director"]:
            params = {"name": utils.get_infolabel("%sListItem.Label" % container_id)}
            start_info_actions("extendedactorinfo", params)
        else:
            utils.notify("Error", "Could not find valid content type")
    elif info == "ratedialog":
        if xbmc.getCondVisibility("System.HasModalDialog"):
            container_id = ""
        else:
            container_id = "Container(%s)" % utils.get_infolabel("System.CurrentControlId")
        dbid = utils.get_infolabel("%sListItem.DBID" % container_id)
        db_type = utils.get_infolabel("%sListItem.DBType" % container_id)
        if db_type == "movie":
            params = {"dbid": dbid,
                      "id": utils.get_infolabel("%sListItem.Property(id)" % container_id),
                      "type": "movie"}
            start_info_actions("ratemedia", params)
        elif db_type == "tvshow":
            params = {"dbid": dbid,
                      "id": utils.get_infolabel("%sListItem.Property(id)" % container_id),
                      "type": "tv"}
            start_info_actions("ratemedia", params)
        if db_type == "episode":
            params = {"tvshow": utils.get_infolabel("%sListItem.TVShowTitle" % container_id),
                      "season": utils.get_infolabel("%sListItem.Season" % container_id),
                      "type": "episode"}
            start_info_actions("ratemedia", params)
    elif info == 'youtubebrowser':
        wm.open_youtube_list(search_str=params.get("id", ""))
    elif info == 'moviedbbrowser':
        if addon.get_global('infodialogs.active'):
            return None
        addon.set_global('infodialogs.active', "true")
        search_str = params.get("id", "")
        if not search_str and params.get("search"):
            result = xbmcgui.Dialog().input(heading=addon.LANG(16017),
                                            type=xbmcgui.INPUT_ALPHANUM)
            if result and result > -1:
                search_str = result
            else:
                addon.clear_global('infodialogs.active')
                return None
        wm.open_video_list(search_str=search_str,
                           mode="search")
        addon.clear_global('infodialogs.active')
    elif info == 'extendedinfo':
        if addon.get_global('infodialogs.active'):
            return None
        addon.set_global('infodialogs.active', "true")
        wm.open_movie_info(movie_id=params.get("id"),
                           dbid=params.get("dbid"),
                           imdb_id=params.get("imdb_id"),
                           name=params.get("name"))
        addon.clear_global('infodialogs.active')
    elif info == 'extendedactorinfo':
        if addon.get_global('infodialogs.active'):
            return None
        addon.set_global('infodialogs.active', "true")
        wm.open_actor_info(actor_id=params.get("id"),
                           name=params.get("name"))
        addon.clear_global('infodialogs.active')
    elif info == 'extendedtvinfo':
        if addon.get_global('infodialogs.active'):
            return None
        addon.set_global('infodialogs.active', "true")
        wm.open_tvshow_info(tmdb_id=params.get("id"),
                            tvdb_id=params.get("tvdb_id"),
                            dbid=params.get("dbid"),
                            imdb_id=params.get("imdb_id"),
                            name=params.get("name"))
        addon.clear_global('infodialogs.active')
    elif info == 'seasoninfo':
        if addon.get_global('infodialogs.active'):
            return None
        addon.set_global('infodialogs.active', "true")
        wm.open_season_info(tvshow=params.get("tvshow"),
                            dbid=params.get("dbid"),
                            season=params.get("season"))
        addon.clear_global('infodialogs.active')
    elif info == 'extendedepisodeinfo':
        if addon.get_global('infodialogs.active'):
            return None
        addon.set_global('infodialogs.active', "true")
        wm.open_episode_info(tvshow=params.get("tvshow"),
                             tvshow_id=params.get("tvshow_id"),
                             dbid=params.get("dbid"),
                             episode=params.get("episode"),
                             season=params.get("season"))
        addon.clear_global('infodialogs.active')
    elif info == 'albuminfo':
        if params.get("id"):
            album_details = AudioDB.get_album_details(params.get("id"))
            utils.dict_to_windowprops(album_details, params.get("prefix", ""))
    elif info == 'artistdetails':
        artist_details = AudioDB.get_artist_details(params["artistname"])
        utils.dict_to_windowprops(artist_details, params.get("prefix", ""))
    elif info == 'ratemedia':
        media_type = params.get("type")
        if not media_type:
            return None
        if params.get("id"):
            tmdb_id = params["id"]
        elif media_type == "movie":
            tmdb_id = tmdb.get_movie_tmdb_id(imdb_id=params.get("imdb_id"),
                                             dbid=params.get("dbid"),
                                             name=params.get("name"))
        elif media_type == "tv" and params.get("dbid"):
            tvdb_id = local_db.get_imdb_id(media_type="tvshow",
                                           dbid=params["dbid"])
            tmdb_id = tmdb.get_show_tmdb_id(tvdb_id=tvdb_id)
        else:
            return False
        rating = utils.input_userrating()
        if rating == -1:
            return None
        tmdb.set_rating(media_type=media_type,
                        media_id=tmdb_id,
                        rating=rating,
                        dbid=params.get("dbid"))
    elif info == 'action':
        for builtin in params.get("id", "").split("$$"):
            xbmc.executebuiltin(builtin)
    elif info == "youtubevideo":
        xbmc.executebuiltin("Dialog.Close(all,true)")
        wm.play_youtube_video(params.get("id", ""))
    elif info == 'playtrailer':
        busy.show_busy()
        if params.get("id"):
            movie_id = params["id"]
        elif int(params.get("dbid", -1)) > 0:
            movie_id = local_db.get_imdb_id(media_type="movie",
                                            dbid=params["dbid"])
        elif params.get("imdb_id"):
            movie_id = tmdb.get_movie_tmdb_id(params["imdb_id"])
        else:
            movie_id = ""
        if movie_id:
            trailers = tmdb.get_movie_videos(movie_id)
            busy.hide_busy()
            time.sleep(0.1)
            if trailers:
                wm.play_youtube_video(trailers[0]["key"])
            elif params.get("title"):
                wm.open_youtube_list(search_str=params["title"])
            else:
                busy.hide_busy()
    elif info == 'deletecache':
        addon.clear_globals()
        for rel_path in os.listdir(addon.DATA_PATH):
            path = os.path.join(addon.DATA_PATH, rel_path)
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
            except Exception as e:
                utils.log(e)
        utils.notify("Cache deleted")
    elif info == 'tmdbpassword':
        addon.set_password_prompt("tmdb_password")
    elif info == 'syncwatchlist':
        pass

