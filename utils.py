def calulate_percentage_lost(responses):
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

def get_addresses(addrs):
    return list(filter(lambda x: not not x, addrs.split(',')))

def get_downtime(last_issue_at):
    from datetime import datetime

    return str(datetime.now() - last_issue_at)

def ping_hosts(host_addresses, ping_count):
  from subprocess import run, PIPE

  responses = []
  for host_address in host_addresses:
    response = run(f'ping -c {ping_count} {host_address}'.split(), stdout=PIPE)
    responses.append(response)

  return responses