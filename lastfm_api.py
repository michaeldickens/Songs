'''

lastfm_api.py
-------------

Author: Michael Dickens
Created: 2019-04-13

Interface to the last.fm API.

'''

from datetime import datetime
from typing import List, Optional, Tuple

import requests


class API:
    def __init__(self, username):
        self.username = username
        self._session = requests.session()
        self.api_key = '93e8621588b59c0ef7fd809fd689a7c1'

    def send_GET(self, method: str, extra_params:Optional[dict] = None) -> requests.Response:
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

    def get_list_of_date_ranges(self) -> List[Tuple[str, str]]:
        response = self.send_GET('user.getweeklychartlist')
        blob = response.json()
        date_ranges = [
            (x['from'], x['to'])
            for x in blob['weeklychartlist']['chart']]
        return date_ranges

    def get_weekly_track_chart(self, from_date: str, to_date: str) -> requests.Response:
        return self.send_GET(
            'user.getweeklytrackchart',
            {
                'from': from_date,
                'to': to_date,
            }
        )

    def get_track_info(self, mbid=None, artist=None, name=None) -> requests.Response:
        # note: the API lets you search by mbid, but it returns "Track not found" for some reason
        body = {'username': self.username}
        if mbid:
            body['mbid'] = mbid
        if artist:
            body['artist'] = artist
        if name:
            body['track'] = name
        return self.send_GET('track.getinfo', body)
