def calculate_percentage_lost(responses):
  from pingparsing import PingParsing

  sent,lost = 0,0
  ping_parser = PingParsing()
  for response in responses:
    results = ping_parser.parse(response.stdout).as_dict()
    sent += results['packet_transmit']
    lost += results['packet_loss_count']

  return (lost/sent) * 100

def calculate_standard_deviation(data, logger):
  from functools import reduce
  from math import sqrt
  from sys import exc_info

  length = len(data)

  if length == 0:
    return
  elif length == 1:
    return data[0], 0

  try:
    mean = reduce(lambda a,b: a+b, data)/length
    deviation = 0
    for i in data:
      deviation += pow((i-mean),2)

    deviation /= (length-1)
  except TypeError as err:
    logger.exception(f'Error: {err}. Likely recieved bad data. Data: {data}')
  except:
    logger.exception(f'Unexpected error: {exc_info()[0]}')
  else:
    return mean, sqrt(deviation)

def format_modem_priority_as_int(priority):
  import re

  pattern = r'.+\((\d)\)$'
  result = re.match(pattern, priority)
  return int(result.group(1))

def format_modem_time_as_datetime(time):
  from datetime import datetime

  time_fmt = '%a %b %d %H:%M:%S %Y'
  return datetime.strptime(time, time_fmt)

def get_addresses(addrs):
  return list(map(lambda x: x.strip(),
    filter(lambda x: not not x, addrs.split(','))
  ))

def get_downtime(last_issue_at):
  from datetime import datetime

  return str(datetime.now() - last_issue_at)

def get_future_event_datetime(events, current_index):
  from datetime import datetime

  future_event_datetime = None
  for log in events[current_index:]:
    try:
      future_event_datetime = format_modem_time_as_datetime(log[0])
    except:
      pass

    if not future_event_datetime == None:
      break

  if future_event_datetime == None:
    return datetime.now()
  return future_event_datetime

def ping_hosts(host_addresses, ping_count):
  from subprocess import run, PIPE

  responses = []
  for host_address in host_addresses:
    response = run(f'ping -c {ping_count} {host_address}'.split(), stdout=PIPE)
    responses.append(response)

  return responses

def remove_none(array):
  return [e for _,e in enumerate(array) if not e == None]
