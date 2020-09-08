from dotenv import load_dotenv, find_dotenv
from mechanicalsoup import StatefulBrowser
from os import getenv
from pprint import pprint

def format_data(data):
  return data.string.encode('ascii', 'ignore').decode('utf-8').strip()

def scrape_page():
  EVENT_PAGE = getenv('MODEM_ADDRESS') + '/MotoSnmpLog.asp'
  browser.open(EVENT_PAGE)

  table_content = browser.get_current_page().find('table', class_='moto-table-content')
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

def login():
  LOGIN_PAGE = getenv('MODEM_ADDRESS')
  browser.open(LOGIN_PAGE)

  form_submit = browser.get_current_page().find('input', class_='moto-login-button')

  form = browser.select_form()
  form.set('loginUsername', getenv('MODEM_USERNAME'))
  form.set('loginPassword', getenv('MODEM_PASSWORD'))
  form.choose_submit(form_submit)
  response = browser.submit_selected()


load_dotenv(find_dotenv())

browser = StatefulBrowser()
browser.set_verbose(2)
login()
scrape_page()