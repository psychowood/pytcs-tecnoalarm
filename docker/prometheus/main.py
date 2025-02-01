import time
from datetime import datetime as dt
import os
from prometheus_client import start_http_server, Gauge
from pytcs_tecnoalarm import TCSSession
from pytcs_tecnoalarm.api_models import ZoneStatusEnum

PREFIX = os.getenv("PREFIX", "")

s = TCSSession(os.getenv("SESSION_KEY"), int(os.getenv("APPID")))

s.get_centrali()

centrale = s.centrali[os.getenv("SERIAL")]

s.select_centrale(centrale.tp)
z = s.get_zones()
p = s.get_programs()

prom_zones = {}
prom_programs = {}

for zone in z.root:
    if zone.status == ZoneStatusEnum.UNKNOWN or not zone.allocated:
        continue

    clean_name = PREFIX + "zone_" + zone.description.replace(" ", "_").replace(".", "_").replace("-", "_").lower()

    thisgauge = Gauge(name=clean_name + "_inFail", documentation="Zone Fail")
    prom_zones[zone.description + "_inFail"] = thisgauge

    thisgauge = Gauge(name=clean_name + "_inLowBattery", documentation="Zone Low Battery")
    prom_zones[zone.description + "_inLowBattery"] = thisgauge

    thisgauge = Gauge(name=clean_name + "_inSupervision", documentation="Zone is in Supervision mode")
    prom_zones[zone.description + "_inSupervision"] = thisgauge

    thisgauge = Gauge(name=clean_name + "_open", documentation="Zone is open")
    prom_zones[zone.description + "_open"] = thisgauge


for programstatus, programdata in zip(p.root, centrale.tp.status.programs):
    if len(programdata.zones) == 0:
        continue

    clean_name = (
        PREFIX + "program_" + programdata.description.replace(" ", "_").replace(".", "_").replace("-", "_").lower()
    )

    thisprogram = Gauge(name=clean_name + "_status", documentation="Program Status")
    prom_programs[programdata.description + "_status"] = thisprogram

    thisprogram = Gauge(name=clean_name + "_alarm", documentation="Program Alarm")
    prom_programs[programdata.description + "_alarm"] = thisprogram

    thisprogram = Gauge(name=clean_name + "_free", documentation="Program Free")
    prom_programs[programdata.description + "_free"] = thisprogram

    thisprogram = Gauge(name=clean_name + "_memAlarm", documentation="Program Mem Alarm")
    prom_programs[programdata.description + "_memAlarm"] = thisprogram

    thisprogram = Gauge(name=clean_name + "_prealarm", documentation="Program Pre Alarm")
    prom_programs[programdata.description + "_prealarm"] = thisprogram


if __name__ == "__main__":
    start_http_server(4567)
    while True:
        time.sleep(10)
        z = s.get_zones()
        for zone in z.root:
            if zone.status == ZoneStatusEnum.UNKNOWN or not zone.allocated:
                continue
            prom_zones[zone.description + "_inFail"].set(zone.inFail)
            prom_zones[zone.description + "_inLowBattery"].set(zone.inLowBattery)
            prom_zones[zone.description + "_inSupervision"].set(zone.inSupervision)
            prom_zones[zone.description + "_open"].set(zone.open)

        p = s.get_programs()
        for programstatus, programdata in zip(p.root, centrale.tp.status.programs):
            if len(programdata.zones) == 0:
                continue

            prom_programs[programdata.description + "_status"].set(programstatus.status)
            prom_programs[programdata.description + "_alarm"].set(programstatus.alarm)
            prom_programs[programdata.description + "_free"].set(programstatus.free)
            prom_programs[programdata.description + "_memAlarm"].set(programstatus.memAlarm)
            prom_programs[programdata.description + "_prealarm"].set(programstatus.prealarm)
        print(dt.now())
