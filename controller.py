'''

controller.py
-------------

Author: Michael Dickens
Created: 2019-04-20

Controller for the JSON DB.

'''

from typing import Dict

import json

from lastfm_api import API

class Controller:
    def __init__(self):
        self.api = API('MTGandP')

        with open('db/weekly_charts.json', 'r') as f:
            json_str = f.read()
            self.weekly_charts = json.loads(json_str)

        self._basic_track_info = {}
        for week in self.weekly_charts:
            for track in week['track']:
                mbid = track['mbid']
                if mbid not in self._basic_track_info:
                    self._basic_track_info[mbid] = {
                        'artist': track['artist']['#text'],
                        'name': track['name'],
                    }


        with open('db/track_info.json', 'r') as f:
            json_str = f.read()
            self.track_info = json.loads(json_str)

    def basic_track_info(self, mbid: str) -> Dict[str, str]:
        return self._basic_track_info[mbid]

    def get_artist(self, mbid: str) -> str:
        return self._basic_track_info[mbid]['artist']

    def get_track_name(self, mbid: str) -> str:
        return self._basic_track_info[mbid]['name']

    def track_id(self, track: dict) -> (str, str):
        return (track['artist']['#text'], track['name'])

    @staticmethod
    def delete_extraneous_data(weekly_charts: dict) -> None:
        for track in weekly_charts['track']:
            if 'image' in track:
                del track['image']

    @staticmethod
    def save_all_track_charts() -> None:
        api = API('MTGandP')
        date_ranges = api.get_list_of_date_ranges()
        date_ranges = date_ranges[-(52+52+26):]
        track_charts = []
        for (from_date, to_date) in date_ranges:
            response = api.get_weekly_track_chart(from_date, to_date)
            data = response.json()['weeklytrackchart']
            delete_extraneous_data(data)
            track_charts.append(data)

        with open('db/weekly_charts.json', 'w') as f:
            data_dump = json.dumps(track_charts)
            f.write(data_dump)

    @staticmethod
    def save_weekly_track_chart() -> None:
        """Save this week's track chart into the JSON db."""
        pass  # TODO

    def save_all_track_info(self) -> None:
        # Note: this does not update tracks that are already in the table, so play counts will become out of date.
        count = 0
        for mbid in self._basic_track_info:
            if mbid not in self.track_info:
                print("on number {}\r".format(count))
                count += 1
                response = self.api.get_track_info(
                    name=self._basic_track_info[mbid]['name'], artist=self._basic_track_info[mbid]['artist'])
                self.track_info[mbid] = response.json()['track']

        with open('db/track_info.json', 'w') as f:
            data_dump = json.dumps(self.track_info)
            f.write(data_dump)

    def weekly_tracks(self):
        for week in self.weekly_charts:
            for track in week['track']:
                yield track
