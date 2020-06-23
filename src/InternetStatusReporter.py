import asyncio
from os import getenv

class InternetStatusReporter:
  def __init__(self):
    from dotenv import load_dotenv, find_dotenv
    from src.utils import get_addresses

    load_dotenv(find_dotenv())
    self.__setup_logger()

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

    self.host_addresses = default_host_addresses + get_addresses(getenv('HOST_ADDRESSES'))
    self.latency_addresses = default_latency_addresses + get_addresses(getenv('LATENCY_ADDRESSES'))
    self.last_issue_at = -1
    self.current_status = self.NETWORK_STATUS['NORMAL']
    self.lock = asyncio.Lock()
    self.db = None

  def __del__(self):
    if self.db != None:
      self.db.close()

  def __is_down(self):
    return self.current_status != self.NETWORK_STATUS['NORMAL']

  def __setup_logger(self):
    from logging import ERROR, INFO, basicConfig, getLogger, Formatter
    from src.MailHandler import MailHandler

    logFormat = '%(asctime)s - %(levelname)s: %(message)s'
    basicConfig(
      filename=getenv('LOG_FILE'),
      filemode='a',
      format=logFormat,
      level=INFO
    )

    mailHandler = MailHandler(
      (getenv('SMTP_SERVER'), getenv('SMTP_PORT')),
      getenv('PI_EMAIL'),
      getenv('MAILTO').split(','),
      'Internet Status Reporter: ERROR!',
      (getenv('PI_EMAIL'), getenv('PI_EMAIL_PASSWORD'))
    )
    mailHandler.setLevel(ERROR)
    mailHandler.setFormatter(Formatter(logFormat))

    self.logger = getLogger('ISR_Logger')
    self.logger.addHandler(mailHandler)
    self.logger.info('InternetStatusReporter is starting up')

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
    from src.utils import calculate_standard_deviation

    results = {}
    for latency_address in self.latency_addresses:
      try:
        runs = int(getenv('LATENCY_RUNS'))
        data = measure_latency(host=latency_address, port=80, runs=runs, timeout=2.5)
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
    from mysql.connector import Error as DB_Error, ProgrammingError, connect, errorcode
    from src.utils import get_downtime

    try:
      self.db = connect(
        database = getenv('DATABASE'),
        host = getenv('DB_HOST'),
        password = getenv('DB_PASSWORD'),
        user = getenv('DB_USERNAME')
      )

      cursor = self.db.cursor()

      sql = 'INSERT INTO `outtages` (`loss`, `downtime`, `created_at`, `maintenance`, `info`) VALUES (%s, %s, %s, %s, %s)'
      values = (loss, get_downtime(self.last_issue_at), datetime.now(), False, info)
      cursor.execute(sql, values)

      self.db.commit()
      cursor.close()
    except ProgrammingError as err:
      if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        self.logger.error(f'Access denied: {err}')
      else:
        self.logger.exception(f'Unexpected error: {err}')
    except DB_Error as err:
      if err.errno == errorcode.ER_BAD_DB_ERROR:
        self.logger.error(f'Database does not exist: {err}')
      else:
        self.logger.exception(f'Unexpected error: {err}')
    finally:
      if self.db != None:
        self.db.close()
        self.db = None
