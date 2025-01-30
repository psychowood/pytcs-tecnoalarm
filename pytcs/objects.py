from datetime import datetime
from pydantic import BaseModel


class HandshakeEntrypoint(BaseModel):
    serviceName: str
    baseUrl: str
    token: str
    expiration: datetime


class HandshakeAccount(BaseModel):
    accountId: int
    backupDate: int
    features: list
    lastLogin: int
    subscriptionDate: int


class HandshakeAnswer(BaseModel):
    appID: int
    entrypoints: list[HandshakeEntrypoint]
    account: HandshakeAccount | None
