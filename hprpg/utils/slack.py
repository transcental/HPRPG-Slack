from hprpg.commands.setup import setup_channels
from hprpg.commands.tidy import tidy_channels
from hprpg.utils.logging import send_heartbeat
from slack_bolt.async_app import AsyncApp

from hprpg.utils.env import env

app = AsyncApp(token=env.slack_bot_token, signing_secret=env.slack_signing_secret)


@app.command("/hprpg-setup")
@app.command("/hprpg-dev-setup")
async def setup(ack, command):
    await ack()
    user_id = command["user_id"]
    if user_id != env.slack_maintainer_id:
        await ack("You are not authorized to run this command.")
        return
    await send_heartbeat("Setting up channels...")
    await setup_channels()
    await send_heartbeat("Setup complete.")


@app.command("/hprpg-tidy")
@app.command("/hprpg-dev-tidy")
async def tidy(ack, command):
    await ack()
    user_id = command["user_id"]
    if user_id != env.slack_maintainer_id:
        await ack("You are not authorized to run this command.")
        return
    await send_heartbeat("Tidying up channels...")
    await tidy_channels()
    await send_heartbeat("Tidy complete.")