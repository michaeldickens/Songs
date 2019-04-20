'''

controller.py
-------------

Author: Michael Dickens
Created: 2019-04-20

Controller for the JSON DB.

'''

from lastfm_api import API

import json

class Controller:
    def __init__(self):
        with open('weekly_charts.json', 'r') as f:
            json_str = f.read()
            self.json_data = json.loads(json_str)

    @staticmethod
    def delete_extraneous_data(json_data: dict) -> None:
        for track in json_data['track']:
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

        with open('weekly_charts.json', 'w') as f:
            data_dump = json.dumps(track_charts)
            f.write(data_dump)

    @staticmethod
    def save_weekly_track_chart() -> None:
        """Save this week's track chart into the JSON db."""
        pass  # TODO
