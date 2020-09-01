import requests
from bs4 import BeautifulSoup
from pprint import pprint

def format_data(data):
  return data.string.encode('ascii', 'ignore').decode('utf-8')

URL = 'http://192.168.100.1/MotoSnmpLog.asp'
page = requests.get(URL)
soup = BeautifulSoup(page.content, 'html.parser')

table_content = soup.find('table', class_='moto-table-content')
for table_row in table_content.find_all('tr'):
  if not 'bgcolor' in table_row.attrs:
    continue
  else:
    data = list(table_row.children)

    time = format_data(data[0])
    priority = format_data(data[1])
    description = format_data(data[2])

    data = [time, priority, description]
    if "".join(data) == "":
      continue

    pprint(data)

def format_data(data):
  return data.string.encode('ascii', 'ignore').decode('utf-8').strip()