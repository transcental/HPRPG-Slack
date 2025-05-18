import json
from hprpg.utils.env import env
from hprpg.types.data.channels import ChannelCategory, Channel
from hprpg.utils.logging import send_heartbeat
from slack_sdk.errors import SlackApiError
import asyncio

async def create_channel(name: str, public: bool):
    """
    Create a channel in Slack.
    """
    try:
        res = await env.slack_client.conversations_create(
            name=name,
            is_private=not public,
        )
    except SlackApiError as e:
        # check if ratelimited
        if e.response["error"] == "ratelimited":
            retry_after = int(e.response.headers.get("Retry-After", 1))
            await asyncio.sleep(retry_after)
            return await create_channel(name, public)
        else:
            raise Exception(f"Failed to create channel: {e}")
    if res["ok"]:
        return res["channel"]["id"]
    else:
        raise Exception(f"Failed to create channel: {res['error']}")


async def update_topic(id: str, topic: str):
    """
    Create a channel in Slack.
    """
    try:
        res = await env.slack_client.conversations_setTopic(
            channel=id,
            topic=topic,
        )
    except SlackApiError as e:
        # check if ratelimited
        if e.response["error"] == "ratelimited":
            retry_after = int(e.response.headers.get("Retry-After", 1))
            await asyncio.sleep(retry_after)
            return await update_topic(id, topic)
        else:
            raise Exception(f"Failed to create channel: {e}")
    if res["ok"]:
        return res["channel"]["id"]
    else:
        raise Exception(f"Failed to create channel: {res['error']}")


async def setup_channels():
    raw_channel_data = open("data/channels.json", "r").read()
    unparsed_channel_data = json.loads(raw_channel_data)
    
    channels = [
        ChannelCategory.parse_obj(category)
        for category in unparsed_channel_data
    ]
    
    for category in channels:
        for channel in category.channels:
            name = f"dev-{channel.name}" if env.environment == "development" else channel.name
            id = await create_channel(name, True)
            await update_topic(id, channel.description)
            await send_heartbeat(f"Created channel {name} in category {category.name}")
