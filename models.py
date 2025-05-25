from datetime import datetime


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

        # Default to using std for time, if not a time then fail
        self.time = datetime.strptime(self.std, "%H:%M")
        self.time_str = self.std

        if self.etd != "On time":
            try:
                # If etd is also a time, display etd (more accurate) with delay
                etime = datetime.strptime(self.etd, "%H:%M")
                minute_diff = int((etime - self.time).total_seconds() // 60)
                self.time = etime
                self.time_str = f"*{self.etd}* ({minute_diff}min delay)"
            except ValueError:
                # If etd is not a time, display std with etd warning
                self.time_str = f"*{self.std}* ({self.etd})"

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
        return self.arrival_point.time < service.arrival_point.time

    def __gt__(self, service):
        return self.arrival_point.time > service.arrival_point.time

    def find_dest(self, destination):
        # Initial check to see if last stop is requested destination
        self.destination_matches = self.destination["crs"] == destination

        if self.destination_matches:
            self.arrival_point = self.call_points[-1]
            self.arrival_str = f"Arrives at {self.arrival_point.time_str}"
        else:
            self.arrival_point = next(
                (x for x in self.call_points if x.crs == destination),
                None
            )
            if self.arrival_point:
                self.arrival_str = (
                    f"Passes {destination} "
                    f"at {self.arrival_point.time_str}"
                )
        return self.arrival_point

    def __str__(self):
        if self.departed:
            return f"Train departed from {self.platform} at {self.atd}"
        else:
            return (
                f"To {self.dest_str}\n"
                f"Departs platform {self.platform} at {self.time_str}\n"
                f"{self.arrival_str}"
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
        except KeyError as k:
            # More legible alternative to key error
            raise KeyError(
                f"Attempted to access key {k} in JSON\n"
                f"Valid keys were: {list(json.keys())}"
            )

