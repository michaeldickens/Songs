'''

controller.py
-------------

Author: Michael Dickens
Created: 2019-04-20

Controller for the JSON DB.

'''

from typing import Dict

import json

from lastfm_api import API, TrackNotFound

class Controller:
    @staticmethod
    def get_artist(track_id: str) -> str:
        return track_id.split('—')[0]  # em-dash

    @staticmethod
    def get_track_name(track_id: str) -> str:
        return track_id.split('—')[1]  # em-dash

    @staticmethod
    def get_track_id(track: dict) -> (str, str):
        # em-dash, should really be en-dash but I screwed it up and now it's in track_info.json
        return '{}—{}'.format(track['artist']['#text'], track['name'])

    @staticmethod
    def load_json(filename: str) -> dict:
        with open('db/{}'.format(filename), 'r') as f:
            json_str = f.read()
            return json.loads(json_str)

    @staticmethod
    def save_json(filename: str, blob: dict) -> None:
        with open('db/{}'.format(filename), 'w') as f:
            data_dump = json.dumps(blob)
            f.write(data_dump)

    def __init__(self):
        self.api = API('MTGandP')

        self.weekly_charts = self.load_json('weekly_charts.json')
        self.track_info = self.load_json('track_info.json')

        self._all_tracks = {}
        for track in self.weekly_tracks():
            # note: this gets overwritten if a track occurs in multiple weeks,
            # so it won't have accurate playcounts
            self._all_tracks[self.get_track_id(track)] = track


    def delete_extraneous_data(self, weekly_charts: dict) -> None:
        for track in weekly_charts['track']:
            if 'image' in track:
                del track['image']

    def save_all_track_charts(self) -> None:
        date_ranges = self.api.get_list_of_date_ranges()
        date_ranges = date_ranges[-(52+52+26):]
        track_charts = []
        for (from_date, to_date) in date_ranges:
            response = self.api.get_weekly_track_chart(from_date, to_date)
            data = response.json()['weeklytrackchart']
            self.delete_extraneous_data(data)
            track_charts.append(data)

        self.save_json('weekly_charts.json', track_charts)

    @staticmethod
    def save_weekly_track_chart() -> None:
        """Save this week's track chart into the JSON db."""
        pass  # TODO

    def save_all_track_info(self) -> None:
        # Note: this does not update tracks that are already in the table, so play counts will become out of date.
        for (count, track_id) in enumerate(self._all_tracks.keys()):
            if track_id not in self.track_info:
                # TODO(2020-06-20): I refactored this to move logic into api.py, haven't tested
                mbid = self._all_tracks[track_id]['mbid']
                artist = self.get_artist(track_id)
                name = self.get_track_name(track_id)
                try:
                    response = self.get_track_info(mbid=mbid, artist=artist, name=name)
                    self.track_info[track_id] = response.json()['track']
                except TrackNotFound as e:
                    print("{} [mbid '{}']: {}".format(track_id, mbid, str(e)))

            if count % 100 == 0:
                print('saving at number {}'.format(count))
                self.save_json('track_info.json', self.track_info)

        self.save_json('track_info.json', self.track_info)

    def weekly_tracks(self):
        for week in self.weekly_charts:
            for track in week['track']:
                yield track
