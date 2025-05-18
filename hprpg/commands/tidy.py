import json
from hprpg.utils.env import env
from hprpg.types.data.channels import ChannelCategory, Channel
from hprpg.utils.logging import send_heartbeat
from slack_sdk.errors import SlackApiError
import asyncio
import time
import logging

all_channels = []

async def find_channel(name: str, cursor: str | None = None):
    """
    Find a channel in Slack by name.
    """
    logging.info(f'Finding {name} | {cursor}')
    global all_channels
    
    # Check if the channel is already in our cached list
    for channel in all_channels:
        if channel["name"] == name:
            return channel["id"]
    
    try:
        # If not found in cache, fetch from Slack API
        cursor = cursor or ""
        res = await env.slack_client.conversations_list(
            exclude_archived=True,
            types="public_channel,private_channel",
            cursor=cursor,
            limit=1000
        )
        
        cursor = res.get("response_metadata", {}).get("next_cursor", None)
        channels = res.get("channels", [])
        all_channels.extend(channels)
        
        for channel in channels:
            if channel["name"] == name:
                return channel["id"]
                
        # If there are more pages, recursively fetch them
        if cursor:
            return await find_channel(name, cursor)
        
        # If we've gone through all pages and still haven't found it
        return None
        
    except SlackApiError as e:
        # check if ratelimited
        if e.response["error"] == "ratelimited":
            retry_after = int(e.response.headers.get("Retry-After", 1))
            logging.info(f"Rate limited, retrying after {retry_after} seconds")
            await asyncio.sleep(retry_after)
            return await find_channel(name, cursor)
        else:
            raise Exception(f"Failed to find channel: {e}")


async def archive_channel(id: str):
    """
    Archive a channel in Slack.
    """
    try:
        res = await env.slack_client.conversations_archive(
            channel=id,
        )
    except SlackApiError as e:
        # check if ratelimited
        if e.response["error"] == "ratelimited":
            retry_after = int(e.response.headers.get("Retry-After", 1))
            await asyncio.sleep(retry_after)
            return await archive_channel(id)
        else:
            raise Exception(f"Failed to archive channel: {e}")
    if res["ok"]:
        return True
    else:
        raise Exception(f"Failed to archive channel: {res['error']}")


async def rename_channel(id: str, name: str):
    """
    Rename a channel in Slack.
    """
    try:
        res = await env.slack_client.conversations_rename(
            channel=id,
            name=name,
        )
    except SlackApiError as e:
        # check if ratelimited
        if e.response["error"] == "ratelimited":
            retry_after = int(e.response.headers.get("Retry-After", 1))
            await asyncio.sleep(retry_after)
            return await rename_channel(id, name)
        else:
            raise Exception(f"Failed to rename channel: {e}")
    if res["ok"]:
        return True
    else:
        raise Exception(f"Failed to rename channel: {res['error']}")


async def tidy_channels():
    raw_channel_data = open("data/channels.json", "r").read()
    unparsed_channel_data = json.loads(raw_channel_data)
    
    channels = [
        ChannelCategory.parse_obj(category)
        for category in unparsed_channel_data
    ]
    
    for category in channels:
        for channel in category.channels:
            name = f"dev-{channel.name}" if env.environment == "development" else channel.name
            channel_id = await find_channel(name)
            if channel_id is None:
                await send_heartbeat(f"Channel {name} not found, skipping...")
                continue

            now = int(time.time())
            id = await rename_channel(channel_id, f"archived-{name}-{now}")
            await archive_channel(channel_id)
            await send_heartbeat(f"Archived channel <#{channel_id}>")
