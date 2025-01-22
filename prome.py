import time
import os
from prometheus_client import start_http_server, Gauge
from tcsession import TCSSession
from api_models import ZoneStatusEnum

s = TCSSession(os.getenv("SESSION_KEY"), int(os.getenv("APPID")))

s.get_centrali()

centrale = s.centrali[os.getenv("PIN")]

s.select_centrale(centrale.tp)
z = s.get_zones()
p = s.get_programs()

prom_zones = {}
prom_programs = {}

for zone in z.root:
    if zone.status == ZoneStatusEnum.UNKNOWN:
        continue
    thisgauge = Gauge(name=zone.description \
        .replace(" ", "_") \
        .replace(".", "_") \
        .replace("-", "_") \
        .lower(), documentation="Zone")
    prom_zones[zone.description] = thisgauge


for programstatus, programdata in zip(p.root, centrale.tp.status.programs):
    if len(programdata.zones) == 0:
        continue

    clean_name = programdata.description.replace(
        "-", "_").replace(" ", "_").lower()

    thisprogram = Gauge(name=clean_name+"_status",
                        documentation="Program Status")
    prom_programs[programdata.description+"_status"] = thisprogram

    thisprogram = Gauge(name=clean_name+"_alarm",
                        documentation="Program Alarm")
    prom_programs[programdata.description+"_alarm"] = thisprogram

    thisprogram = Gauge(name=clean_name+"_free", documentation="Program Free")
    prom_programs[programdata.description+"_free"] = thisprogram

    thisprogram = Gauge(name=clean_name+"_memAlarm",
                        documentation="Program Mem Alarm")
    prom_programs[programdata.description+"_memAlarm"] = thisprogram

    thisprogram = Gauge(name=clean_name+"_prealarm",
                        documentation="Program Pre Alarm")
    prom_programs[programdata.description+"_prealarm"] = thisprogram


if __name__ == '__main__':
    start_http_server(4567)
    while True:
        time.sleep(10)
        z = s.get_zones()
        for zone in z.root:
            if zone.status == ZoneStatusEnum.UNKNOWN:
                continue
            prom_zones[zone.description].set(zone.open)

        p = s.get_programs()
        for programstatus, programdata in zip(p.root, centrale.tp.status.programs):
            if len(programdata.zones) == 0:
                continue
            prom_programs[programdata.description +
                          "_status"].set(programstatus.status)
            prom_programs[programdata.description +
                          "_alarm"].set(programstatus.alarm)
            prom_programs[programdata.description +
                          "_free"].set(programstatus.free)
            prom_programs[programdata.description +
                          "_memAlarm"].set(programstatus.memAlarm)
            prom_programs[programdata.description +
                          "_prealarm"].set(programstatus.prealarm)
        print("Done!")
