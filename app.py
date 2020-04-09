import asyncio
import ipdb
from logging import INFO, basicConfig, getLogger
from os import getenv

class InternetStatusReporter:
  def __init__(self, host_addresses = []):
    from dotenv import load_dotenv, find_dotenv

    load_dotenv(find_dotenv())
    self.__setup_logger()

    self.NETWORK_STATUS = {
      'NORMAL': 0,
      'DEGRADED': 1,
      'DOWN': 2
    }

    default_addresses = [
      '1.1.1.1',
      '8.8.8.8',
      '8.8.4.4',
      '139.130.4.5'
    ]
    self.host_addresses = default_addresses + host_addresses
    self.last_issue_at = -1
    self.current_status = self.NETWORK_STATUS['NORMAL']
    self.lock = asyncio.Lock()
    self.db = None

  def __del__(self):
    if self.db != None:
      self.db.close()

  def __downtime(self):
    from datetime import datetime

    return str(datetime.now() - self.last_issue_at)

  def __is_down(self):
    return self.current_status != self.NETWORK_STATUS['NORMAL']

  def __setup_logger(self):
    basicConfig(
      filename=getenv('LOG_FILE'),
      filemode='a',
      format='%(asctime)s - %(levelname)s: %(message)s',
      level=INFO
    )
    self.logger = getLogger('ISR_Logger')
    self.logger.info('InternetStatusReporter is starting up')

  async def run(self):
    loss = self.evaluate(self.ping_hosts())
    if self.__is_down():
      await self.lock.acquire()
      while(self.lock.locked()):
        self.evaluate(self.ping_hosts())

      self.report_issue(loss, self.__downtime())

  def ping_hosts(self):
    from subprocess import run, PIPE

    responses = []
    for host_address in self.host_addresses:
      response = run(f'ping -c5 {host_address}'.split(), stdout=PIPE)
      responses.append(response)

    return responses

  def evaluate(self, responses):
    from pingparsing import PingParsing

    stats = {
      'sent': 0,
      'lost': 0
    }
    ping_parser = PingParsing()
    for response in responses:
      results = ping_parser.parse(response.stdout).as_dict()
      stats['sent'] += results['packet_transmit']
      stats['lost'] += results['packet_loss_count']

    return self.calculate_status(stats)

  def calculate_status(self, stats):
    from datetime import datetime
    percentage_lost = (stats['lost'] / stats['sent']) * 100

    if percentage_lost == 0.0:
      if self.current_status != self.NETWORK_STATUS['NORMAL']:
        self.logger.info('Internet is back to normal')
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

    return percentage_lost

  def report_issue(self, loss, downtime):
    from datetime import datetime
    from mysql.connector import Error as DB_Error, connect, errorcode

    try:
      self.db = connect(
        database = getenv('DATABASE'),
        host = getenv('HOST'),
        password = getenv('PASSWORD'),
        user = getenv('USERNAME')
      )

      cursor = self.db.cursor()

      sql = 'INSERT INTO `outtages` (`loss`, `downtime`, `created_at`) VALUES (%s, %s, %s)'
      values = (loss, str(downtime), datetime.now())
      cursor.execute(sql, values)

      self.db.commit()
      cursor.close()
    except DB_Error as err:
      if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        self.logger.error(f'Access denied: {err}')
      elif err.errno == errorcode.ER_BAD_DB_ERROR:
        self.logger.error(f'Database does not exist: {err}')
      else:
        self.logger.critical(f'Unexpected error: {err}')
    finally:
      if self.db != None:
        self.db.close()
        self.db = None

if __name__ == "__main__":
  isr = InternetStatusReporter()
  loop = asyncio.get_event_loop()
  loop.run_until_complete(isr.run())
  
