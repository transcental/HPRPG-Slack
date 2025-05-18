from pydantic import BaseModel, ConfigDict


class Channel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    description: str


class ChannelCategory(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    channels: list[Channel]