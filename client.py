'''

client.py
---------

Author: Michael Dickens
Created: 2019-04-20

'''

from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Tuple

from lastfm_api import TrackNotFound
from controller import Controller


def get_ranks(mapping):
    ordered = sorted(mapping.items(), key=lambda pair: -pair[1])
    return {k: rank+1 for (rank, (k, v)) in enumerate(ordered)}


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
            print("{:>2}. {:<25} – {:<25} [{:>4} plays, {:>4}:{:02}]".format(
                rank+1,
                artist,
                album,
                playcount[key],
                int((time/1000)/60), int((time/1000) % 60)
            ))

    return time_listened


def biggest_time_gainers_and_losers(playcount: Dict[str, int], time_listened: Dict[str, int],
                                    print_result=True) -> Dict[str, float]:
    def _print(rank, track_id, delta):
        time = time_listened[track_id]
        print("{:>2}. {:<25} – {:<25} [{:>2} plays, {:>3}:{:02}, up {:.1f}% ({:>4} to {:>4})]".format(
            rank+1,
            controller.get_artist(track_id),
            controller.get_track_name(track_id),
            playcount[track_id],
            int((time/1000)/60), int((time/1000) % 60),
            delta * 100,
            max(playcount_rank[track_id], time_listened_rank[track_id]),
            min(playcount_rank[track_id], time_listened_rank[track_id]),
        ))

    playcount_rank = get_ranks(playcount)
    time_listened_rank = get_ranks(time_listened)

    rank_delta = {}
    for track_id in playcount_rank.keys() & time_listened_rank.keys():
        if time_listened[track_id] != 0:
            rank_delta[track_id] = (playcount_rank[track_id] / time_listened_rank[track_id])

    ordered_deltas = sorted(rank_delta.items(), key=lambda pair: pair[1])

    if print_result:
        print("Shortest but most frequent songs:")
        for rank, (track_id, delta) in enumerate(ordered_deltas[:10]):
            _print(rank, track_id, 1 - delta)

        print("\n---\n")
        print("Rarest but longest songs:")
        for rank, (track_id, delta) in enumerate(reversed(ordered_deltas[(-10):])):
            _print(rank, track_id, 1 - (1 / delta))

    return rank_delta


def combined_ranking(playcount: Dict[str, int], time_listened: Dict[str, int], print_result=True) -> Dict[str, int]:
    playcount_rank = get_ranks(playcount)
    time_listened_rank = get_ranks(time_listened)
    combined = {k: playcount_rank[k] + time_listened_rank[k] for k in playcount.keys() & time_listened.keys()}
    combined_rank = get_ranks(combined)
    ordered_tracks = sorted(combined_rank.items(), key=lambda pair: -pair[1])

    if print_result:
        for rank, (track_id, _) in enumerate(ordered_tracks[:25]):
            print("{:>2}. {:<25} – {:25}".format(
                rank + 1,
                controller.get_artist(track_id),
                controller.get_track_name(track_id),
            ))

    return combined_rank




def forgotten_scores_v1(controller):
    time_since_plays = {}
    playcount = {}
    today = datetime.today()
    for week in controller.weekly_charts:
        date = datetime.fromtimestamp(int(week['@attr']['from']))
        for track in week['track']:
            track_id = controller.get_track_id(track)
            playcount[track_id] = playcount.get(track_id, 0) + int(track['playcount'])
            time_since_plays[track_id] = time_since_plays.get(track_id, 0) + (today - date).days

    track_scores = {}
    for track_id in time_since_plays:
        track_scores[track_id] = time_since_plays[track_id]**2 / playcount[track_id]**(1/2.0)

    ranked = sorted(track_scores.items(), key=lambda pair: -pair[1])

    for (track_id, score) in ranked[:20]:
        print("{:>4}: {:<25} – {:<35} ({:>2} plays)".format(
            int(score), controller.get_artist(track_id), controller.get_track_name(track_id),
            playcount[track_id]))


def forgotten_scores_v2(controller):
    '''Weight by time since last listen multiplied by the Nth root of play count for some N.'''
    last_play = {}
    playcount = {}
    today = datetime.today()
    for week in controller.weekly_charts:
        date = datetime.fromtimestamp(int(week['@attr']['from']))
        for track in week['track']:
            track_id = controller.get_track_id(track)
            last_play[track_id] = date
            playcount[track_id] = playcount.get(track_id, 0) + int(track['playcount'])

    track_scores = {}
    for track_id in last_play:
        last_play_delta = (today - last_play[track_id]).days
        track_scores[track_id] = last_play_delta * playcount[track_id]**(1/4.0)

    ranked = sorted(track_scores.items(), key=lambda pair: -pair[1])

    for (track_id, score) in ranked[:20]:
        print("{:>4}: {:<25} – {:<35} ({:>2} plays, {} last play)".format(
            int(score), controller.get_artist(track_id), controller.get_track_name(track_id),
            playcount[track_id], last_play[track_id].strftime("%Y-%m-%d")))


def forgotten_scores_v3(controller):
    '''Apply exponential weighting to listens and find tracks where the
    exponentially-weighted play count is small relative to unweighted play
    count.'''
    exp_wt_plays = {}
    playcount = {}
    today = datetime.today()
    for i, week in enumerate(controller.weekly_charts):
        date = datetime.fromtimestamp(int(week['@attr']['from']))
        for track in week['track']:
            track_id = controller.get_track_id(track)
            exp_wt_plays[track_id] = exp_wt_plays.get(track_id, 0) + int(track['playcount']) * 2**(-(len(controller.weekly_charts) - i) / 52)
            playcount[track_id] = playcount.get(track_id, 0) + int(track['playcount'])

    track_scores = {}
    for track_id in playcount:
        track_scores[track_id] = -(exp_wt_plays[track_id] + 1) / (playcount[track_id] + 1)

    ranked = sorted(track_scores.items(), key=lambda pair: -pair[1])

    for (track_id, score) in ranked[:20]:
        print("{:>4}: {:<25} – {:<35} ({:>2} plays, {:.1f} exp-weighted plays)".format(
            int(score), controller.get_artist(track_id), controller.get_track_name(track_id),
            playcount[track_id], exp_wt_plays[track_id]))


controller = Controller()
# playcount = track_playcounts(controller)
# time_listened = longest_listened_songs(controller, print_result=False)
# combined_ranking(playcount, time_listened)
forgotten_scores_v3(controller)
