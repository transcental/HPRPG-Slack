import asyncio
import contextlib
import logging

import uvicorn
from aiohttp import ClientSession
from dotenv import load_dotenv
from starlette.applications import Starlette

from hprpg.utils.env import env
from hprpg.utils.logging import send_heartbeat

load_dotenv()

try:
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

logging.basicConfig(level="INFO" if env.environment != "production" else "WARNING")


@contextlib.asynccontextmanager
async def main(_app: Starlette):
    await send_heartbeat(":magic_wand: Bot is online!")
    async with ClientSession() as session:
        env.session = session
        handler = None
        if env.slack_app_token:
            from slack_bolt.adapter.socket_mode.async_handler import (
                AsyncSocketModeHandler,
            )
            from hprpg.utils.slack import app as slack_app

            handler = AsyncSocketModeHandler(slack_app, env.slack_app_token)
            logging.info("Starting Socket Mode handler")
            await handler.connect_async()

        logging.info(f"Starting Uvicorn app on port {env.port}")

        yield

        if handler:
            logging.info("Stopping Socket Mode handler")
            await handler.close_async()


def start():
    uvicorn.run(
        "hprpg.utils.starlette:app",
        host="0.0.0.0",
        port=env.port,
        log_level="info" if env.environment != "production" else "warning",
        reload=env.environment == "development",
    )


if __name__ == "__main__":
    start()
