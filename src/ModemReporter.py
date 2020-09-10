from os import getenv

class ModemReporter:
  def __init__(self):
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())

    MODEM_ADDRESS = getenv('MODEM_ADDRESS')

    self.__setup_browser()
    self.db = None
    self.pages = {
      'home': MODEM_ADDRESS,
      'event_log': MODEM_ADDRESS + '/MotoSnmpLog.asp'
    }

  def __del__(self):
    if self.db != None:
      self.db.close()

  def __setup_browser(self):
    from mechanicalsoup import StatefulBrowser

    self.browser = StatefulBrowser()
    self.browser.set_verbose(2)

  def run(self):
    self.login()
    self.scrape_events()

  def login(self):
    self.browser.open(self.pages['home'])

    submit_button = self.browser.get_current_page().find('input', class_='moto-login-button')

    form = self.browser.select_form()
    form.set('loginUsername', getenv('MODEM_USERNAME'))
    form.set('loginPassword', getenv('MODEM_PASSWORD'))
    form.choose_submit(submit_button)

    self.browser.submit_selected()

  def report_events(self, events):
    from mysql.connector import Error as DB_Error, ProgrammingError, connect, errorcode
    from utils import format_modem_priority_as_int, format_modem_time_as_datetime

    try:
      self.db = connect(
        database = getenv('DATABASE'),
        host = getenv('DB_HOST'),
        password = getenv('DB_PASSWORD'),
        user = getenv('DB_USERNAME')
      )

      cursor = self.db.cursor()
      sql = 'INSERT INTO `modem_events` (`description`, `priority`, `created_at`, `maintenance`) VALUES (%s, %s, %s, %s)'

      for event in events:
        time, priority, description = event
        created_at = str(format_modem_time_as_datetime(time))

        values = (description, format_modem_priority_as_int(priority), created_at, False)
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

  def scrape_events(self):
    from pprint import pprint

    self.browser.open(self.pages['event_log'])

    table_content = self.browser.get_current_page().find('table', class_='moto-table-content')

    event_logs = []
    for table_row in table_content.find_all('tr'):
      if not 'bgcolor' in table_row.attrs:
        continue
      else:
        data = list(table_row.children)

        time = data[0].string.strip()
        priority = data[1].string.strip()
        description = data[2].string.strip()

        data = [time, priority, description]
        if "".join(data) == "":
          continue

        event_logs.append(data)
        pprint(data)
    
    return event_logs

  
mr = ModemReporter()
mr.run()