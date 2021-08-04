from deemon.app import Deemon, utils, download, notify
import time
import tqdm
import logging
import deezer

logger = logging.getLogger(__name__)

# class Refresh(Deemon):
#
#     def __init__(self, skip_download=False, time_machine=None):
#         super().__init__()
#
#         self.skip_download = skip_download
#         self.todays_date = utils.get_todays_date()
#         self.time_machine = False
#
#         if self.skip_download:
#             logger.debug("--skip-download has been set, releases will only be added to the database")
#
#         if time_machine:
#             if utils.validate_date(time_machine):
#                 self.todays_date = time_machine
#                 self.time_machine = True
#                 logger.info(f"+ Time machine activated! Today is {time_machine}")
#             else:
#                 logger.error(f"Time machine date is invalid: {time_machine}")
#                 exit()
#
#         self.dz = deezer.Deezer()
#         self.new_release_count = 0
#         self.monitored_artists = []
#         self.monitored_playlists = []
#         self.queue_list = []
#         self.new_releases = []
#
#     def is_future_release(self, album_release):
#         if album_release > self.todays_date:
#             return 1
#         else:
#             return 0
#
#     def construct_new_release_list(self, release_date, artist, album, cover):
#         for days in self.new_releases:
#             for key in days:
#                 if key == "release_date":
#                     if release_date in days[key]:
#                         days["releases"].append({'artist': artist, 'album': album, 'cover': cover})
#                         return
#
#         self.new_releases.append({'release_date': release_date, 'releases': [{'artist': artist, 'album': album}]})
#
#     def refresh_playlists(self):
#         logger.debug("Refreshing playlists")
#         found_new_tracks = False
#         self.monitored_playlists = self.db.get_all_monitored_playlists()
#
#         if not self.monitored_playlists:
#             return
#
#         progress = tqdm.tqdm(self.monitored_playlists, ascii=" #",
#                              bar_format='{desc}...  {n_fmt}/{total_fmt} [{bar:40}] {percentage:3.0f}%')
#
#         for item in progress:
#             progress.set_description_str(f"Refreshing playlists")
#             new_playlist = False
#             playlist = self.dz.api.get_playlist(item[0])
#             playlist_exists = self.db.get_playlist_by_id(playlist['id'])
#             if not playlist_exists:
#                 logger.debug("Playlist is newly added, no downloads this round...")
#                 new_playlist = True
#             for track in playlist['tracks']['data']:
#                 vals = {'playlist_id': playlist['id'],
#                         'track_id': track['id'],
#                         'track_name': track['title'],
#                         'artist_id': track['artist']['id'],
#                         'artist_name': track['artist']['name'],
#                         'track_added': int(time.time())}
#
#                 sql_check_exists = "SELECT * FROM 'playlist_tracks' " \
#                                    "WHERE track_id = :track_id AND playlist_id = :playlist_id"
#
#                 playlist_track_exists = self.db.query(sql_check_exists, vals).fetchone()
#
#                 if not playlist_track_exists:
#                     found_new_tracks = True
#                     if not new_playlist:
#                         logger.info(f"New track added to playlist {playlist['title']}: {track['artist']['name']} - {track['title']}")
#                     self.db.query("INSERT INTO 'playlist_tracks' "
#                                   "('track_id', 'playlist_id', 'artist_id', "
#                                   "'artist_name', 'track_name', 'track_added') "
#                                   "VALUES (:track_id, :playlist_id, :artist_id, :artist_name, "
#                                   ":track_name, :track_added)", vals)
#             if found_new_tracks and not new_playlist:
#                 self.queue_list.append(download.QueueItem(url=playlist['link'], playlist=playlist['title']))
#                 #TODO separate download jobs between refreshes; currently artists refresh handles job
#
#     def refresh(self, artist_id=None):
#         self.refresh_playlists()
#         logger.debug(f"Refreshing artists")
#         if artist_id:
#             self.monitored_artists = self.db.get_monitored_artist_by_id(id=artist_id)
#         else:
#             self.monitored_artists = self.db.get_all_monitored_artists()
#
#         if len(self.monitored_artists) == 0:
#             logger.info("At least one artist needs to be monitored before you can refresh!")
#             return
#
#         progress = tqdm.tqdm(self.monitored_artists, ascii=" #",
#                              bar_format='{desc}...  {n_fmt}/{total_fmt} [{bar:40}] {percentage:3.0f}%')
#
#         for artist in progress:
#             self.new_release_count = 0
#             new_artist = False
#             artist = {"id": artist[0], "name": artist[1], "bitrate": self.config["bitrate"], "record_type": artist[3]}
#             progress.set_description_str(f"Refreshing artists")
#             artist_exists = self.db.get_artist_by_id(artist_id=artist["id"])
#             albums = self.dz.api.get_artist_albums(artist["id"])
#
#             if not artist_exists:
#                 new_artist = True
#                 logger.debug(f"New artist detected: {artist['name']}, future releases will be downloaded")
#
#             if new_artist:
#                 if len(albums["data"]) == 0:
#                     logger.warning(f"WARNING: Artist '{artist['name']}' setup for monitoring but no releases were found.")
#
#             for album in albums["data"]:
#
#                 already_exists = self.db.get_album_by_id(album_id=album["id"])
#
#                 if already_exists:
#                     release = [x for x in already_exists]
#                     _album = {
#                         'artist_id': release[0],
#                         'artist_name': release[1],
#                         'album_id': release[2],
#                         'album_name': release[3],
#                         'release_date': release[4],
#                         'future_release': release[6]
#                     }
#
#                     if _album["future_release"] and (_album["release_date"] <= self.todays_date):
#                         logger.info(f"Artist: {_album['artist_name']} ** Pre-release has now been released "
#                                     f"and will be downloaded **")
#                         self.db.reset_future(_album['album_id'])
#                     else:
#                         continue
#                 else:
#                     release_in_future = self.is_future_release(album["release_date"])
#                     if release_in_future:
#                         if self.time_machine:
#                             continue
#                         logger.debug(f"[PRE-RELEASE DETECTED] {artist['name']} - {album['title']} detected as a pre-release; "
#                                      f"will be released on {album['release_date']}")
#                     self.db.add_new_release(
#                         artist["id"],
#                         artist["name"],
#                         album["id"],
#                         album["title"],
#                         album["release_date"],
#                         future_release=release_in_future
#                     )
#
#                 if self.skip_download or new_artist:
#                     continue
#
#                 if (self.config["record_type"] == album["record_type"]) or (self.config["record_type"] == "all"):
#                     if self.config["release_by_date"]:
#                         max_release_date = utils.get_max_release_date(self.config["release_max_days"])
#                         if album['release_date'] < max_release_date:
#                             logger.debug(f"Release '{artist['name']} - {album['title']}' skipped, too old...")
#                             continue
#                         self.new_release_count += 1
#                     logger.debug(f"queue: added {artist['name']} - {album['title']} to the queue")
#                     self.queue_list.append(download.QueueItem(artist, album))
#                     self.construct_new_release_list(album['release_date'], artist['name'],
#                                                     album['title'], album['cover_medium'])
#
#             if self.new_release_count > 0:
#                 logger.info(f"{artist['name']}: {self.new_release_count} new release(s)")
#
#         logger.debug("Refresh complete")
#         if self.queue_list:
#             print("")
#             dl = download.Download()
#             dl.download_queue(self.queue_list)
#         self.db.commit()
#
#         if len(self.new_releases) > 0 and self.config["alerts"] == 1:
#             notification = notify.Notify(self.new_releases)
#             notification.send()


class Refresh:

    def __init__(self, artist_id=None, playlist_id=None, skip_download=False, time_machine=None):
        self.artist_id = artist_id
        self.playlist_id = playlist_id
        self.skip_download = skip_download
        self.time_machine = time_machine
        self.total_new_releases = 0
        self.queue_list = []
        self.new_releases = []
        self.refresh_date = self.set_refresh_date()
        self.db = Deemon().db
        self.config = Deemon().config
        self.dz = deezer.Deezer()
        self.run()

    def set_refresh_date(self):
        if self.time_machine:
            if utils.validate_date(self.time_machine):
                return self.time_machine
            else:
                return False
        else:
            return utils.get_todays_date()

    def run(self):
        if not self.refresh_date:
            logger.error(f"Error while setting time machine to {self.time_machine}")

        if self.playlist_id or self.monitoring_playlists():
            self.refresh_playlists()

        if self.artist_id or self.monitoring_artists():
            self.refresh_artists()

        if len(self.queue_list) > 0:
            dl = download.Download()
            dl.download_queue(self.queue_list)

        self.db.commit()

    def refresh_playlists(self):
        logger.debug("Refreshing playlists")
        new_track_count = 0
        if self.playlist_id:
            monitored = []
            for i in self.playlist_id:
                monitored.append(self.db.get_monitored_playlists_by_id(i))
        else:
            monitored = self.db.get_all_monitored_playlists()

            progress = tqdm.tqdm(monitored, ascii=" #",
                                 bar_format='{desc}...  {n_fmt}/{total_fmt} [{bar:40}] {percentage:3.0f}%')

            for plist in progress:
                new_playlist = self.existing_playlist(plist[0])
                playlist = self.dz.api.get_playlist(plist[0])
                progress.set_description_str("Refreshing playlists")

                if new_playlist:
                    logger.debug(f"New playlist: {plist[1]}")
                    

    def refresh_artists(self):
        logger.debug("Refreshing artists")
        if self.artist_id:
            monitored = []
            for i in self.artist_id:
                monitored.append(self.db.get_monitored_artist_by_id(i))
        else:
            monitored = self.db.get_all_monitored_artists()

        progress = tqdm.tqdm(monitored, ascii=" #",
                             bar_format='{desc}...  {n_fmt}/{total_fmt} [{bar:40}] {percentage:3.0f}%')

        for artist in progress:
            artist = {"id": artist[0], "name": artist[1], "bitrate": self.config["bitrate"], "record_type": artist[3]}
            artist_new_release_count = 0
            new_artist = self.existing_artist(artist['id'])
            progress.set_description_str("Refreshing artists")
            artist_albums = self.dz.api.get_artist_albums(artist['id'])

            if new_artist:
                logger.debug(f"New artist: '{artist['name']}'")
                if len(artist_albums['data']) == 0:
                    logger.warning(f"WARNING: Artist '{artist['name']}' setup for monitoring but no releases were found.")

            for album in artist_albums['data']:
                exists = self.db.get_album_by_id(album_id=album['id'])
                if exists:
                    if exists['future_release'] and (exists['release_date'] <= self.refresh_date):
                        logger.debug(f"Pre-release released: {exists['artist_name']} - {exists['album_name']}")
                        self.db.reset_future(exists['album_id'])
                    else:
                        continue

                future = self.is_future_release(album['release_date'])
                if future:
                    if self.time_machine:
                        continue
                    logger.debug(f"Pre-release detected: {artist['name']} - {album['title']} [{album['release_date']}]")

                self.db.add_new_release(artist['id'], artist['name'], album['id'],
                                        album['title'], album['release_date'], future_release=future)

                if self.skip_download or new_artist:
                    continue

                if ((self.config['record_type'] == album['record_type']) or
                        (self.config['record_type'] == "all")):
                    if self.config['release_by_date']:
                        max_release_date = utils.get_max_release_date(self.config['release_max_days'])
                        if album['release_date'] < max_release_date:
                            logger.debug(f"Skipping release, too old... {artist['name']} - {album['title']}")
                            continue
                    self.total_new_releases += 1
                    logger.debug(f"Adding to queue: {artist['name']} - {album['title']}")
                    self.queue_list.append(download.QueueItem(artist, album))
                    self.append_new_release(album['release_date'], artist['name'],
                                            album['title'], album['cover_medium'])
            if artist_new_release_count > 0:
                logger.info(f"{artist['name']}: {artist_new_release_count} new release(s)")

    def is_future_release(self, release_date):
        if release_date > self.refresh_date:
            return 1
        else:
            return 0

    def monitoring_playlists(self):
        query = "SELECT * FROM 'playlists'"
        result = self.db.query(query).fetchone()
        if len(result) > 0:
            return True

    def monitoring_artists(self):
        query = "SELECT * FROM 'monitor'"
        result = self.db.query(query).fetchone()
        if len(result) > 0:
            return True

    def existing_artist(self, artist_id):
        sql_values = {'artist_id': artist_id}
        # TODO BUG - issue #25 - Artist treated as new artist until at least one release has been seen
        query = "SELECT * FROM 'releases' WHERE artist_id = :artist_id"
        artist_exists = self.db.query(query, sql_values).fetchone()
        if not artist_exists:
            return True

    def existing_playlist(self, playlist_id):
        sql_values = {'playlist_id': playlist_id}
        # TODO BUG - issue #25 - Artist treated as new artist until at least one release has been seen
        query = "SELECT * FROM 'playlist_tracks' WHERE playlist_id = :playlist_id"
        playlist_exists = self.db.query(query, sql_values).fetchone()
        if not playlist_exists:
            return True

    def append_new_release(self, release_date, artist, album, cover):
        for days in self.new_releases:
            for key in days:
                if key == "release_date":
                    if release_date in days[key]:
                        days["releases"].append({'artist': artist, 'album': album, 'cover': cover})
                        return

        self.new_releases.append({'release_date': release_date, 'releases': [{'artist': artist, 'album': album}]})
