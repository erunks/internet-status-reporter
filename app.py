import asyncio
from src.InternetStatusReporter import InternetStatusReporter

if __name__ == "__main__":
  isr = InternetStatusReporter()
  loop = asyncio.get_event_loop()
  loop.run_until_complete(isr.run())
