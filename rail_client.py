import requests
from models import DepartureBoard


class RailClient:
    def __init__(self):
        self.base_url = (
            "https://api1.raildata.org.uk/"
            "1010-live-departure-board-dep1_2/LDBWS/api/20220120"
        )

        self.endpoints = {
            "departures": {
                "url": self.base_url + "/GetDepBoardWithDetails/{}",
                "token": "ATOKEN"  # TODO: Load from config file
            },
            "services": {
                "url": self.base_url + "/ServiceDetails/{}",
                "token": "ATOKEN"  # TODO: Load from config file
            }
        }

        self.services = []

    def get_headers(self, token):
        return {
            "x-apikey": token,
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/136.0.0.0 Safari/537.36"
            )
        }

    def query_endpoint(self, endpoint, param):
        conn_details = self.endpoints[endpoint]
        response = requests.get(
            conn_details["url"].format(param),
            headers=self.get_headers(conn_details["token"])
        )
        response.raise_for_status()
        return response.json()

    def get_departures(self, origin, destination):
        json = self.query_endpoint("departures", origin)

        dpb = DepartureBoard(json)
        self.services = dpb.get_services_by_dest(destination)
        self.services.sort()

        if self.services:
            return_list = []
            for i, x in enumerate(self.services):
                return_list.append(str(i+1) + " " + str(x))

            return_list.append(
                "\nSelect a service to track with the syntax 'Track [n]'"
            )
            reply = "\n".join(return_list)
        else:
            reply = "No suitable services found for this query!"

        return reply
