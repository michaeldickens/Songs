'''

client.py
---------

Author: Michael Dickens
Created: 2019-04-20

'''

from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Tuple

from controller import Controller


def track_playcounts(controller):
    playcount = {}
    for track in controller.weekly_tracks():
        track_id = controller.get_track_id(track)
        playcount[track_id] = playcount.get(track_id, 0) + int(track['playcount'])

    return playcount


def longest_listened_songs(controller, print_result=True) -> Dict[str, int]:
    """
    Rank songs by how long the user has spent listening to them. Note that this
    can be unreliable in some cases when last.fm incorrectly reports the song
    duration as 0.
    """
    playcount = track_playcounts(controller)

    time_listened = {
        track_id: int(controller.track_info[track_id]['duration']) * playcount[track_id]
        for track_id in (playcount.keys() & controller.track_info.keys())
    }

    top_songs = sorted(time_listened.items(), key=lambda pair: -pair[1])

    if print_result:
        for (rank, (track_id, time)) in enumerate(top_songs[:25]):
            print("{:>2}. {:<25} – {:<35} [{:>2} plays, {:>3}:{:02}]".format(
                rank+1,
                controller.get_artist(track_id),
                controller.get_track_name(track_id),
                playcount[track_id],
                int((time/1000)/60), int((time/1000) % 60)
            ))

    return time_listened


def _longest_listened(controller, key_fn: Callable[[str], Any]) -> Tuple[Dict[str, int], Dict[str, int], List[Tuple[str, int]]]:
    track_playcount = track_playcounts(controller)
    top_songs = longest_listened_songs(controller, print_result=False)
    time_listened = {}

    for track_id in top_songs:
        key = key_fn(track_id)
        if key is not None:
            time_listened[key] = time_listened.get(key, 0) + top_songs[track_id]

    top_keys = sorted(time_listened.items(), key=lambda pair: -pair[1])

    key_playcount = {}
    for track_id in track_playcount:
        key = key_fn(track_id)
        key_playcount[key] = key_playcount.get(key, 0) + track_playcount[track_id]

    return (key_playcount, time_listened, top_keys)


def longest_listened_artists(controller, print_result=True) -> Dict[str, int]:
    playcount, time_listened, top_keys = _longest_listened(
        controller, lambda track_id: controller.get_artist(track_id), print_result=print_result)

    if print_result:
        for (rank, (artist, time)) in enumerate(top_keys[:25]):
            print("{:>2}. {:<25} [{:>4} plays, {:>4}:{:02}]".format(
                rank+1,
                artist,
                playcount[artist],
                int((time/1000)/60), int((time/1000) % 60)
            ))

    return time_listened


def longest_listened_albums(controller, print_result=True) -> Dict[str, int]:
    def get_album(track_id):
        if controller.track_info.get(track_id, {}).get('album', {}).get('title') is None:
            return None
        return "{}—{}".format(
            controller.get_artist(track_id),
            controller.track_info[track_id]['album']['title'])

    playcount, time_listened, top_keys = _longest_listened(controller, get_album)

    if print_result:
        for (rank, (key, time)) in enumerate(top_keys[:25]):
            artist, album = key.split('—')
            print("{:>2}. {:<25} – {:<35} [{:>4} plays, {:>4}:{:02}]".format(
                rank+1,
                artist,
                album,
                playcount[key],
                int((time/1000)/60), int((time/1000) % 60)
            ))

    return time_listened


def forgotten_scores_v1(controller):
    time_since_plays = {}
    playcount = {}
    today = datetime.today()
    for week in controller.weekly_charts:
        date = datetime.fromtimestamp(int(week['@attr']['from']))
        for track in week['track']:
            mbid = track['mbid']
            playcount[mbid] = playcount.get(mbid, 0) + int(track['playcount'])
            time_since_plays[mbid] = time_since_plays.get(mbid, 0) + (today - date).days

    track_scores = {}
    for mbid in time_since_plays:
        track_scores[mbid] = time_since_plays[mbid]**2 / playcount[mbid]**(1/2.0)

    ranked = sorted(track_scores.items(), key=lambda pair: -pair[1])

    for (mbid, score) in ranked[:20]:
        basic_track_info = controller.basic_track_info(mbid)
        print("{:>4}: {:<25} – {:<35} ({:>2} plays)".format(
            int(score), basic_track_info['artist'], basic_track_info['name'],
            playcount[mbid]))


def forgotten_scores_v2(controller):
    last_play = {}
    playcount = {}
    today = datetime.today()
    for week in controller.weekly_charts:
        date = datetime.fromtimestamp(int(week['@attr']['from']))
        for track in week['track']:
            mbid = track['mbid']
            last_play[mbid] = date
            playcount[mbid] = playcount.get(mbid, 0) + int(track['playcount'])

    track_scores = {}
    for mbid in last_play:
        last_play_delta = (today - last_play[mbid]).days
        track_scores[mbid] = last_play_delta * playcount[mbid]**(1/8.0)

    ranked = sorted(track_scores.items(), key=lambda pair: -pair[1])

    for (mbid, score) in ranked[:20]:
        basic_track_info = controller.basic_track_info(mbid)
        print("{:>4}: {:<25} – {:<35} ({:>2} plays, {} last play)".format(
            int(score), basic_track_info['artist'], basic_track_info['name'],
            playcount[mbid], last_play[mbid].strftime("%Y-%m-%d")))


controller = Controller()
longest_listened_songs(controller)
