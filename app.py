import asyncio
import sentry_sdk
from dotenv import load_dotenv, find_dotenv
from os import getenv
from src.InternetStatusReporter import InternetStatusReporter

load_dotenv(find_dotenv())

sentry_sdk.init(
  getenv('SENTRY_DSN'),
  traces_sample_rate=1.0,
)

if __name__ == "__main__":
  isr = InternetStatusReporter()
  loop = asyncio.get_event_loop()
  loop.run_until_complete(isr.run())
