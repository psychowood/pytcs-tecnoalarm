from datetime import datetime
import uuid
import time
from requests import Session
from objects import HandshakeAnswer
from api_models import TcsTpsList, TcsMonitor, TcsTpReply, TcsTpstatus, TcsProgram, TcsZones, TcsLogs, TcsTpRequest
from exceptions import OTPException


class Centrale():
    model_prefix_map = {
        45: "tp888",
        38: "tp042"
    }
    code: str
    codes: list
    description: str
    icon: str
    idx: int
    ip: None
    keys: list
    monitor: TcsMonitor
    passphTCS: str
    port: int
    programs: list
    rcmds: list
    remotes: list
    sn: str
    tp: TcsTpReply
    type: int
    zones: list

    def __init__(self, session: "TCSSession", tp:TcsTpReply):
        self.sn = tp.sn
        self.type = tp.type
        self.session = session
        self.tp = tp
        self.monitor = None

    def get_monitor(self):
        r = self.session.get(
            f"/tcs/monitor/{self.model_prefix_map[self.type]}.{self.sn}")
        assert r.ok

        self.monitor = TcsMonitor.model_validate_json(r.text)


class TCSSession(Session):
    appid: str
    base_url = "https://evolution.tecnoalarm.com"
    token: str
    expiration: datetime
    centrali: dict[str, Centrale]

    def __init__(self, token: str = None, appid: str = None):
        super().__init__()
        self.token = token
        self.appid = appid
        self.expiration = None
        self.centrali = {}
        self.headers.update({
            "lang": "en"
        })

        if token is not None and appid is not None:
            self.re_auth()

    def re_auth(self):
        self.headers.update({
            "token": self.token,
            "App-ID": str(self.appid)
        })

        self.handshake()

    def handshake(self):
        r = self.get("/account/handshake")
        assert r.ok
        ans = HandshakeAnswer.model_validate(r.json())

        self.token = None
        self.expiration = None
        self.appid = ans.appID
        for x in ans.entrypoints:
            if x.serviceName == "TCS service":
                self.token = x.token
                self.expiration = x.expiration

                break

        if self.token is None or self.expiration is None:
            raise ValueError("Token not found")

        self.headers.update({"Auth": self.token})

    def login(self, email: str, password: str, otp: str = None):
        if self.token is None:
            self.handshake()

        params = {} if otp is None else {"otp": otp}

        r = self.post("/account/login", params=params, json={
            "email": email,
            "hash": password
        })

        if r.status_code == 202:
            raise OTPException()
        elif r.status_code == 404:
            raise ValueError("User or password don't match")

        # post token to /app
        self.headers.update({
            "TCS-Token": str(uuid.uuid4()),
            "so": "fa king"
        })
        self.put("/tcs/app", json=[])

    def get_centrali(self):
        r = self.get("/tcs/tps")
        assert r.ok

        centrali = TcsTpsList.model_validate_json(r.text)

        for x in centrali.root:
            if x.code not in self.centrali:
                self.centrali[x.code] = Centrale(self, x)

    def select_centrale(self, centrale: TcsTpReply):
        self.delete("/tcs/tp")
        if centrale.status is None:
            r = self.post("/tcs/tp", json=centrale.model_dump())
            assert r.ok

            while True:
                r = self.get("/tcs/tpstatus", params={"quick": "true"})
                assert r.ok

                if r.status_code == 200:
                    break
                else:
                    time.sleep(0.2)

            centrale.status = TcsTpstatus.model_validate_json(r.text)

        req_data = TcsTpRequest.model_validate(centrale.model_dump())
        r = self.post("/tcs/tp", json=req_data.model_dump())
        if not r.ok:
            print(r.json())
        return r.ok

    def get_programs(self):
        r = self.get("/tcs/program")
        assert r.ok

        return TcsProgram.model_validate_json(r.text)

    def get_zones(self):
        r = self.get("/tcs/zone")
        assert r.ok

        return TcsZones.model_validate_json(r.text)

    def get_logs(self):
        r = self.get("/tcs/log/0")
        assert r.ok

        return TcsLogs.model_validate_json(r.text)

    def request(self, method, url, *args, **kwargs):
        url = self.base_url + url
        return super().request(method, url, *args, **kwargs)
