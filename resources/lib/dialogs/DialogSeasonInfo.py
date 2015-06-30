# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

from ..Utils import *
from ..TheMovieDB import *
from ..YouTube import *
from ..ImageTools import *
from DialogBaseInfo import DialogBaseInfo
from ..WindowManager import wm
from ..OnClickHandler import OnClickHandler
from .. import VideoPlayer

ch = OnClickHandler()
PLAYER = VideoPlayer.VideoPlayer()


class DialogSeasonInfo(DialogBaseInfo):

    @busy_dialog
    def __init__(self, *args, **kwargs):
        super(DialogSeasonInfo, self).__init__(*args, **kwargs)
        self.type = "Season"
        self.tmdb_id = kwargs.get('id')
        self.season = kwargs.get('season')
        self.tvshow = kwargs.get('tvshow')
        if not self.season or not (self.tmdb_id and self.tvshow):
            return None
        data = extended_season_info(tmdb_tvshow_id=self.tmdb_id,
                                    tvshow_name=self.tvshow,
                                    season_number=self.season)
        if data:
            self.info, self.data = data
        else:
            return None
        search_str = "%s %s tv" % (self.info["TVShowTitle"], self.info['title'])
        youtube_thread = GetYoutubeVidsThread(search_str=search_str)
        youtube_thread.start()
        if "dbid" not in self.info:  # need to add comparing for seasons
            self.info['poster'] = get_file(url=self.info.get("poster", ""))
        filter_thread = FilterImageThread(self.info.get("poster", ""), 25)
        filter_thread.start()
        youtube_thread.join()
        filter_thread.join()
        self.info['ImageFilter'] = filter_thread.image
        self.info['ImageColor'] = filter_thread.imagecolor
        self.listitems = [(1000, self.data["actors"]),
                          (750, self.data["crew"]),
                          (2000, self.data["episodes"]),
                          (1150, self.data["videos"]),
                          (1250, self.data["images"]),
                          (1350, self.data["backdrops"]),
                          (350, youtube_thread.listitems)]
        self.listitems = [(a, create_listitems(b)) for a, b in self.listitems]

    def onInit(self):
        super(DialogSeasonInfo, self).onInit()
        pass_dict_to_skin(data=self.info,
                          prefix="movie.",
                          window_id=self.window_id)
        self.fill_lists()

    def onClick(self, control_id):
        ch.serve(control_id, self)

    @ch.click(750)
    @ch.click(1000)
    def open_actor_info(self):
        wm.open_actor_info(prev_window=self,
                           actor_id=self.control.getSelectedItem().getProperty("id"))

    @ch.click(2000)
    def open_episode_info(self):
        wm.open_episode_info(prev_window=self,
                             tvshow=self.tvshow,
                             tvshow_id=self.tmdb_id,
                             season=self.control.getSelectedItem().getProperty("season"),
                             episode=self.control.getSelectedItem().getProperty("episode"))

    @ch.click(350)
    @ch.click(1150)
    def play_youtube_video(self):
        PLAYER.play_youtube_video(youtube_id=self.control.getSelectedItem().getProperty("youtube_id"),
                                  listitem=self.control.getSelectedItem(),
                                  window=self)

    @ch.click(1250)
    @ch.click(1350)
    def open_image(self):
        wm.open_slideshow(image=self.control.getSelectedItem().getProperty("original"))

    @ch.click(132)
    def open_text(self):
        wm.open_textviewer(header=LANG(32037),
                           text=self.info["Plot"],
                           color=self.info['ImageColor'])
