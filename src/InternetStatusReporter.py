import asyncio
from os import getenv
from src.DatabaseInteractor import DatabaseInteractor
from src.ModemReporter import ModemReporter

class InternetStatusReporter(DatabaseInteractor):
  def __init__(self):
    from dotenv import load_dotenv, find_dotenv
    from src.utils import get_addresses

    super().__init__()

    load_dotenv(find_dotenv())

    self.NETWORK_STATUS = {
      'NORMAL': 0,
      'DEGRADED': 1,
      'DOWN': 2
    }

    default_host_addresses = [
      '1.1.1.1',
      '8.8.8.8',
      '8.8.4.4',
      '139.130.4.5'
    ]
    default_latency_addresses = [
      'amazon.com',
      'cloudflare.com',
      'google.com',
      'youtube.com'
    ]

    self.modemReporter = ModemReporter()
    self.host_addresses = default_host_addresses + get_addresses(getenv('HOST_ADDRESSES'))
    self.latency_addresses = default_latency_addresses + get_addresses(getenv('LATENCY_ADDRESSES'))
    self.last_issue_at = -1
    self.current_status = self.NETWORK_STATUS['NORMAL']
    self.lock = asyncio.Lock()

  def __is_down(self):
    return self.current_status != self.NETWORK_STATUS['NORMAL']

  async def run(self):
    loss = self.check_status()
    info = self.measure_latency()
    if self.__is_down():
      await self.lock.acquire()
      while(self.lock.locked()):
        self.check_status()

      if info == '':
        info = self.measure_latency()

      self.report_issue(loss, info)

  def check_status(self):
    from src.utils import calculate_percentage_lost, ping_hosts

    percentage_lost = calculate_percentage_lost(
      ping_hosts(self.host_addresses, getenv('PING_COUNT'))
    )
    self.update_status(percentage_lost)

    return percentage_lost

  def update_status(self, percentage_lost):
    from datetime import datetime

    if percentage_lost == 0.0:
      if self.current_status != self.NETWORK_STATUS['NORMAL']:
        self.logger.info('Internet is back to normal')
        self.modemReporter.run()
        self.lock.release()

      self.current_status = self.NETWORK_STATUS['NORMAL']
    else:
      if self.current_status == self.NETWORK_STATUS['NORMAL']:
        self.logger.warning(f'Internet is degraded or down. Percentage lost at: {percentage_lost}')
        self.last_issue_at = datetime.now()

      if percentage_lost == 100.0:
        self.current_status = self.NETWORK_STATUS['DOWN']
      else:
        self.current_status = self.NETWORK_STATUS['DEGRADED']

  def measure_latency(self):
    from json import dumps
    from sys import exc_info
    from tcp_latency import measure_latency
    from src.utils import calculate_standard_deviation, remove_none

    results = {}
    for latency_address in self.latency_addresses:
      try:
        runs = int(getenv('LATENCY_RUNS'))
        data = measure_latency(host=latency_address, port=80, runs=runs, timeout=2.5)
        data = remove_none(data)
        mean, deviation = calculate_standard_deviation(data, self.logger)
      except:
        self.logger.exception(f'Unexpected error: {exc_info()[0]}')
      else:
        results[latency_address] = {
          'deviation': deviation,
          'max': max(data),
          'mean': mean,
          'min': min(data)
        }

    return dumps(results)

  def report_issue(self, loss, info = ''):
    from datetime import datetime
    from src.utils import get_downtime

    try:
      self.connect_database()

      sql = 'INSERT INTO `outtages` (`loss`, `downtime`, `created_at`, `maintenance`, `info`) VALUES (%s, %s, %s, %s, %s)'
      values = (loss, get_downtime(self.last_issue_at), datetime.now(), False, info)
      self.execute_sql_with_commit(sql, values)
    except:
      self.logger.exception(f'Unexpected error: {exc_info()[0]}')
    finally:
      self.disconnect_database()
