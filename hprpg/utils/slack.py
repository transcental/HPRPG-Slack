from slack_bolt.async_app import AsyncApp

from hprpg.utils.env import env

app = AsyncApp(token=env.slack_bot_token, signing_secret=env.slack_signing_secret)
