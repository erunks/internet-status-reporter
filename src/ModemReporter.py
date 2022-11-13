from src.DatabaseInteractor import DatabaseInteractor

class ModemReporter(DatabaseInteractor):
  def __init__(self):
    from os import getenv

    super().__init__()

    MODEM_ADDRESS = getenv('MODEM_ADDRESS')

    self.__setup_browser()
    self.pages = {
      'event_log': MODEM_ADDRESS + '/MotoSnmpLog.asp',
      'home': MODEM_ADDRESS,
      'logout': MODEM_ADDRESS + '/logout.asp'
    }
    self.enabled = bool(int(getenv('MODEM_REPORTING')))

  def __setup_browser(self):
    from mechanicalsoup import StatefulBrowser

    self.browser = StatefulBrowser(soup_config={'features': 'html.parser'})
    self.browser.set_verbose(2)

  def run(self):
    if self.enabled:
        self.login()
        self.report_events(self.scrape_events())
        self.logout()

  def filter_event_logs(self, event_logs):
    last_event = self.get_last_logged_event()

    if last_event == None:
      return event_logs

    last_event_datetime = last_event[2]
    return [event_log for _,event_log in enumerate(event_logs) if event_log[0] > last_event_datetime]

  def get_last_logged_event(self):
    from sys import exc_info
    result = None

    try:
      self.connect_database()

      sql = "SELECT * FROM `modem_events` ORDER BY `id` DESC LIMIT 1"
      result = self.execute_sql_and_get_results(sql)
      self.disconnect_database()

    except:
      self.logger.exception(f'Unexpected error: {exc_info()[0]}')

    if len(result) == 0:
      return None
    return list(result[0])

  def login(self):
    from os import getenv

    self.browser.open(self.pages['home'])

    submit_button = self.browser.get_current_page().find('input', class_='moto-login-button')

    form = self.browser.select_form()
    form.set('loginUsername', getenv('MODEM_USERNAME'))
    form.set('loginPassword', getenv('MODEM_PASSWORD'))
    form.choose_submit(submit_button)

    self.browser.submit_selected()

  def logout(self):
    self.browser.open(self.pages['logout'])

  def report_events(self, events):
    from sys import exc_info
    from src.utils import format_modem_priority_as_int, format_modem_time_as_datetime, get_future_event_datetime

    try:
      self.connect_database()
      sql = "INSERT INTO `modem_events` (`description`, `priority`, `created_at`, `maintenance`) VALUES "
      value_string = '("%s", %s, "%s", %s)'

      event_datetime = None
      value_list = []
      for index,event in enumerate(events):
        time, priority, description = event
        try:
          event_datetime = format_modem_time_as_datetime(time)
        except:
          if event_datetime == None:
            event_datetime = get_future_event_datetime(events, index)

        created_at = str(event_datetime)

        values = (description, format_modem_priority_as_int(priority), created_at, False)

        value_list.append(value_string % values)

      full_sql_string = sql + ", ".join(value_list)
      self.execute_sql_with_commit(full_sql_string)

      self.disconnect_database()

    except:
      self.logger.exception(f'Unexpected error: {exc_info()[0]}')

  def scrape_events(self):
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

    return event_logs
