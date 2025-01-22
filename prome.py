import time
import os
from prometheus_client import start_http_server, Gauge
from tcsession import TCSSession
from api_models import ZoneStatusEnum

PREFIX = os.getenv("PREFIX", "")

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
    thisgauge = Gauge(name=PREFIX+"zone_"+zone.description
                      .replace(" ", "_")
                      .replace(".", "_")
                      .replace("-", "_")
                      .lower(), documentation="Zone")
    thisgauge.labels()
    prom_zones[zone.description] = thisgauge


for programstatus, programdata in zip(p.root, centrale.tp.status.programs):
    if len(programdata.zones) == 0:
        continue

    clean_name = PREFIX+"program_"+programdata.description.replace(
        "-", "_").replace(" ", "_").lower()

    thisprogram = Gauge(name=clean_name,
                        documentation="Program",
                        labelnames=["status", "alarm", "free", "memAlarm", "prealarm"])
    prom_programs[programdata.description] = thisprogram

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

            prom_programs[programdata.description].labels(
                status=programstatus.status,
                alarm=programstatus.alarm,
                free=programstatus.free,
                memAlarm=programstatus.alarm,
                prealarm=programstatus.prealarm
            )
        print("Done!")
