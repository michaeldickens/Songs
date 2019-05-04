'''

client.py
---------

Author: Michael Dickens
Created: 2019-04-20

'''

from datetime import datetime, timedelta
from typing import Dict

from controller import Controller


def track_playcounts(controller):
    playcount = {}
    for track in controller.weekly_tracks():
        mbid = track['mbid']
        playcount[mbid] = playcount.get(mbid, 0) + int(track['playcount'])

    return playcount


def longest_listened_songs(controller, print_result=True) -> Dict[str, int]:
    playcount = track_playcounts(controller)

    time_listened = {
        mbid: int(controller.track_info[mbid]['duration']) * playcount[mbid]
        for mbid in (playcount.keys() & controller.track_info.keys())
    }

    top_songs = sorted(time_listened.items(), key=lambda pair: -pair[1])

    if print_result:
        for (rank, (mbid, time)) in enumerate(top_songs[:50]):
            print("{:>2}. {:<25} – {:<35} [{:>2} plays, {:>3}:{:02}]".format(
                rank+1,
                controller.get_artist(mbid),
                controller.get_track_name(mbid),
                playcount[mbid],
                int((time/1000)/60), int((time/1000) % 60)
            ))

    return time_listened


def longest_listened_artists(controller, print_result=True) -> Dict[str, int]:
    track_playcount = track_playcounts(controller)
    top_songs = longest_listened_songs(controller, print_result=False)
    time_listened = {}

    for mbid in top_songs:
        artist = controller.get_artist(mbid)
        time_listened[artist] = time_listened.get(artist, 0) + top_songs[mbid]

    top_artists = sorted(time_listened.items(), key=lambda pair: -pair[1])

    artist_playcount = {}
    for mbid in track_playcount:
        artist = controller.get_artist(mbid)
        artist_playcount[artist] = artist_playcount.get(artist, 0) + track_playcount[mbid]

    if print_result:
        for (rank, (artist, time)) in enumerate(top_artists[:25]):
            print("{:>2}. {:<25} [{:>4} plays, {:>4}:{:02}]".format(
                rank+1,
                artist,
                artist_playcount[artist],
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
top_songs = longest_listened_songs(controller)
import ipdb; ipdb.set_trace()
