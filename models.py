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
                # TODO: split this into datetime and display str vars?
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
