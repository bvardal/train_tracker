import re
import requests
from datetime import datetime


class TelegramClient:
    def __init__(self):
        self.last_update_id = 0
        self.last_updates = []
        self.base_url = "https://api.telegram.org/bot"
        self.base_url += "ATOKEN"  # TODO: Load from config file

        self.endpoints = {
            "updates": self.base_url + "/getUpdates"
        }

    def fetch_updates(self):
        response = requests.get(
            self.base_url + "/getUpdates",
            {"timeout": 30, "offset": self.last_update_id}
        )
        response.raise_for_status()
        self.last_updates = response.json().get("result", [])

    def get_last_message(self):
        if not self.last_updates:
            return None
        else:
            last_result = self.last_updates[-1]

        self.last_update_id = last_result["update_id"] + 1
        message = last_result["message"]

        if not message["from"]["is_bot"]:
            return {
                "chat_id": message["chat"]["id"],
                "text": message["text"]
            }
        else:
            return None

    def send_message(self, payload):
        response = requests.post(self.base_url + "/sendMessage", data=payload)
        response.raise_for_status()
        return response

    def respond_to_request(self):
        message = self.get_last_message()

        if not message:
            return

        text = message["text"].upper()
        m = re.search(r"([A-Z]{3}) TO ([A-Z]{3})", text)
        if not m:
            message["text"] = "Unrecognised format"
            return self.send_message(message)

        origin, destination = m.group(1), m.group(2)
        client = RailClient()

        message["text"] = client.get_departures(origin, destination)
        return self.send_message(message)


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


class Station:
    def __init__(self, json):
        # Values that should always exist
        self.crs = json["crs"]
        self.name = json["locationName"]

    def __str__(self):
        return f"{self.crs} ({self.name})"


class TimingDetails:
    def __init__(self, json, is_service):
        # If station is origin or service, then add "d" for departure
        self.std = json["st" + is_service*"d"]
        self.etd = json["et" + is_service*"d"]

        if self.etd == "On time":
            self.time = self.std  # If on time, use scheduled
        else:
            t1 = datetime.strptime(self.std, "%H:%M")
            try:
                # If both std and etd are times, prefer etd with delay in min
                t2 = datetime.strptime(self.etd, "%H:%M")
                minute_diff = int((t2 - t1).total_seconds() // 60)
                self.time = f"{self.etd} ({minute_diff}min delay)"
            except ValueError:
                # If etd is not a time, display std and etd string
                self.time = f"{self.std} ({self.etd})"

        # Values that may not exist
        self.platform = json.get("platform") or "TBA"
        self.sta = json.get("sta")
        self.eta = json.get("eta")
        self.atd = json.get("atd")

        self.departed = bool(self.atd)  # If an atd is recorded, is departed


class Service(TimingDetails):
    def __init__(self, json):
        super().__init__(json, True)
        self.destination = json["destination"][0]
        self.dest_str = (
                f"{self.destination['locationName']} "
                f"({self.destination['crs']})"
        )
        json_points = json["subsequentCallingPoints"][0]["callingPoint"]
        self.call_points = [CallingPoint(x) for x in json_points]

    def __lt__(self, service):
        return self.arrival_point.time[0:5] < service.arrival_point.time[0:5]

    def __gt__(self, service):
        return self.arrival_point.time[0:5] > service.arrival_point.time[0:5]

    def find_dest(self, destination):
        # Initial check to see if last stop is requested destination
        self.destination_matches = self.destination["crs"] == destination

        if self.destination_matches:
            self.arrival_point = self.call_points[-1]
            self.arrival_str = f"arriving at {self.arrival_point.time}"
        else:
            self.arrival_point = next(
                (x for x in self.call_points if x.crs == destination),
                None
            )
            if self.arrival_point:
                self.arrival_str = (
                    f"passing {destination} "
                    f"at {self.arrival_point.time}"
                )
        return self.arrival_point

    def __str__(self):
        if self.departed:
            return f"Train departed from {self.platform} at {self.atd}"
        else:
            return (
                f"Train to {self.dest_str} departing platform {self.platform}"
                f" at {self.time} and {self.arrival_str}"
            )


class DepartureBoard(Station):
    def __init__(self, json):
        super().__init__(json)
        self.services = [Service(x) for x in json["trainServices"]]

    def get_services_by_dest(self, destination):
        return [x for x in self.services if bool(x.find_dest(destination))]


class CallingPoint(Station, TimingDetails):
    def __init__(self, json):
        Station.__init__(self, json)
        try:
            TimingDetails.__init__(self, json, False)
        except KeyError:
            print(json)
