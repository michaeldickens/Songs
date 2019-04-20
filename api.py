'''

api.py
------

Author: Michael Dickens
Created: 2019-04-13

'''

from datetime import datetime

import requests


class User:
    def __init__(self, username):
        self.username = username
        self._session = requests.session()
        self.api_key = '93e8621588b59c0ef7fd809fd689a7c1'

    def send_GET(self, method, extra_params=None):
        if extra_params is None:
            extra_params = {}
        return self._session.get(
            'https://ws.audioscrobbler.com/2.0/',
            params=dict(
                method=method,
                user=self.username,
                api_key=self.api_key,
                format='json',
                **extra_params
            )
        )

    def get_list_of_date_ranges(self):
        response = self.send_GET('user.getweeklychartlist')
        blob = response.json()
        date_ranges = [
            (x['from'], x['to'])
            for x in blob['weeklychartlist']['chart']]
        return date_ranges

    def get_weekly_track_chart(self, from_date, to_date):
        return self.send_GET(
            'user.getweeklytrackchart',
            {
                'from': from_date,
                'to': to_date,
            }
        )


user = User('MTGandP')
date_ranges = user.get_list_of_date_ranges()
response = user.get_weekly_track_chart(date_ranges[-1][0], date_ranges[-1][1])
import ipdb; ipdb.set_trace()
