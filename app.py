import asyncio
import ipdb
from os import getenv

class InternetStatusReporter:
  def __init__(self):
    from dotenv import load_dotenv, find_dotenv

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

    self.host_addresses = default_host_addresses + self.__get_addresses(getenv('HOST_ADDRESSES'))
    self.latency_addresses = default_latency_addresses + self.__get_addresses(getenv('LATENCY_ADDRESSES'))
    self.last_issue_at = -1
    self.current_status = self.NETWORK_STATUS['NORMAL']
    self.lock = asyncio.Lock()
    self.db = None

  def __del__(self):
    if self.db != None:
      self.db.close()

  def __calculate_deviation(self, data):
    from functools import reduce
    from math import sqrt

    length = len(data)
    mean = reduce(lambda a,b: a+b, data)/length
    deviation = 0
    for i in data:
      deviation += pow((i-mean),2)

    deviation /= (length-1)
    return mean, sqrt(deviation)

  def __downtime(self):
    from datetime import datetime

    return str(datetime.now() - self.last_issue_at)

  def __get_addresses(self, addrs):
    return list(filter(lambda x: not not x, addrs.split(',')))

  def __is_down(self):
    return self.current_status != self.NETWORK_STATUS['NORMAL']

  def __setup_logger(self):
    from logging import ERROR, INFO, basicConfig, getLogger, Formatter
    from mailHandler import MailHandler

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
    loss = self.evaluate(self.ping_hosts())
    info = self.measure_latency()
    if self.__is_down():
      await self.lock.acquire()
      while(self.lock.locked()):
        self.evaluate(self.ping_hosts())

      if info == '':
        info =  self.measure_latency()

      self.report_issue(loss, self.__downtime(), info)

  def ping_hosts(self):
    from subprocess import run, PIPE

    ping_count = getenv('PING_COUNT')
    responses = []
    for host_address in self.host_addresses:
      response = run(f'ping -c {ping_count} {host_address}'.split(), stdout=PIPE)
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

  def measure_latency(self):
    from json import dumps
    from sys import exc_info
    from tcp_latency import measure_latency

    results = {}
    try:
      for latency_address in self.latency_addresses:
        runs = int(getenv('LATENCY_RUNS'))
        data = measure_latency(host=latency_address, port=80, runs=runs, timeout=2.5)
        mean, deviation = self.__calculate_deviation(data)
        results[latency_address] = {
          'deviation': deviation,
          'max': max(data),
          'mean': mean,
          'min': min(data)
        }
    except:
      self.logger.exception(f'Unexpected error: {exc_info()[0]}')
    else:
      return dumps(results)
    
    return ''

  def report_issue(self, loss, downtime, info = ''):
    from datetime import datetime
    from mysql.connector import Error as DB_Error, ProgrammingError, connect, errorcode

    try:
      self.db = connect(
        database = getenv('DATABASE'),
        host = getenv('DB_HOST'),
        password = getenv('DB_PASSWORD'),
        user = getenv('DB_USERNAME')
      )

      cursor = self.db.cursor()

      sql = 'INSERT INTO `outtages` (`loss`, `downtime`, `created_at`, `maintenance`, `info`) VALUES (%s, %s, %s, %s, %s)'
      values = (loss, downtime, datetime.now(), False, info)
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

if __name__ == "__main__":
  isr = InternetStatusReporter()
  loop = asyncio.get_event_loop()
  loop.run_until_complete(isr.run())
