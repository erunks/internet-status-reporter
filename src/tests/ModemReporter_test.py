import unittest
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from freezegun import freeze_time
from unittest.mock import MagicMock, patch
from src.ModemReporter import ModemReporter

load_dotenv(find_dotenv(".env.test"), override=True)

MODEM_ADDRESS = 'http://0.0.0.0'

BROWSER_MOCK = MagicMock()
CONNECTION_MOCK = MagicMock()
EVENT_LOGS = [
  [datetime(2020, 9, 13, 9, 00, 00), 2, "This is the description"],
  [datetime(2020, 9, 14, 17, 45, 00), 6, "This is another description"],
  [datetime(2020, 9, 15, 13, 30, 00), 4, "This is the last description"]
]

class TestModemReporter(unittest.TestCase):
  @classmethod
  def setUpClass(self):
    print('------------------------------ ModemReporter Tests ------------------------------')
    self.modemReporter = ModemReporter()
    self.modemReporter.browser = BROWSER_MOCK
    self.modemReporter.connection = CONNECTION_MOCK
    self.modemReporter.logger = MagicMock()

  def setUp(self):
    self.resetMocks()

  @classmethod
  def tearDownClass(self):
    self.modemReporter.disconnect_database()

  @classmethod
  def resetMocks(self):
    BROWSER_MOCK.reset_mock()
    CONNECTION_MOCK.reset_mock()
    CONNECTION_MOCK.cursor.return_value = None
    self.modemReporter.logger.reset_mock()

  @patch('mechanicalsoup.StatefulBrowser')
  def test__setup_browser(self, browser_mock):
    browser_mock.return_value = BROWSER_MOCK

    self.modemReporter._ModemReporter__setup_browser()

    browser_mock.assert_called_once()
    BROWSER_MOCK.set_verbose.assert_called_once_with(2)

  @patch.object(ModemReporter, 'get_last_logged_event')
  def test_filter_event_logs_when_new_event_logs(self, get_last_logged_event_mock):
    get_last_logged_event_mock.return_value = ["Some string", 2, datetime(2020, 9, 11, 14, 10, 25), 0]

    self.assertEqual(
      self.modemReporter.filter_event_logs(EVENT_LOGS),
      EVENT_LOGS
    )

  @patch.object(ModemReporter, 'get_last_logged_event')
  def test_filter_event_logs_when_no_new_event_logs(self, get_last_logged_event_mock):
    get_last_logged_event_mock.return_value = ["Some string", 2, datetime(2020, 9, 16, 14, 10, 25), 0]

    self.assertEqual(
      self.modemReporter.filter_event_logs(EVENT_LOGS),
      []
    )

  @patch.object(ModemReporter, 'get_last_logged_event')
  def test_filter_event_logs_when_no_last_event(self, get_last_logged_event_mock):
    get_last_logged_event_mock.return_value = None

    self.assertEqual(
      self.modemReporter.filter_event_logs(EVENT_LOGS),
      EVENT_LOGS
    )

  @patch('mysql.connector.connect')
  def test_get_last_logged_event(self, connect_mock):
    SQL_QUERY = "SELECT * FROM `modem_events` ORDER BY `id` DESC LIMIT 1"
    SQL_RESPONSE = [("Some string", 2, datetime(2020, 9, 15, 14, 10, 25), 0)]

    cursor_mock = MagicMock()
    cursor_mock.fetchall.return_value = SQL_RESPONSE
    CONNECTION_MOCK.cursor.return_value = cursor_mock
    connect_mock.return_value = CONNECTION_MOCK

    self.assertEqual(
      self.modemReporter.get_last_logged_event(),
      ["Some string", 2, datetime(2020, 9, 15, 14, 10, 25), 0]
    )

    connect_mock.assert_called_once()
    CONNECTION_MOCK.cursor.assert_called_once()
    cursor_mock.execute.assert_called_once_with(SQL_QUERY)
    cursor_mock.fetchall.assert_called_once()
    cursor_mock.close.assert_called_once()
    CONNECTION_MOCK.close.assert_called_once()

  @patch('mysql.connector.connect')
  def test_get_last_logged_event_when_no_records_present(self, connect_mock):
    SQL_QUERY = "SELECT * FROM `modem_events` ORDER BY `id` DESC LIMIT 1"
    SQL_RESPONSE = []

    cursor_mock = MagicMock()
    cursor_mock.fetchall.return_value = SQL_RESPONSE
    CONNECTION_MOCK.cursor.return_value = cursor_mock
    connect_mock.return_value = CONNECTION_MOCK

    self.assertEqual(
      self.modemReporter.get_last_logged_event(),
      None
    )

    connect_mock.assert_called_once()
    CONNECTION_MOCK.cursor.assert_called_once()
    cursor_mock.execute.assert_called_once_with(SQL_QUERY)
    cursor_mock.fetchall.assert_called_once()
    cursor_mock.close.assert_called_once()
    CONNECTION_MOCK.close.assert_called_once()

  def test_login(self):
    form_mock = MagicMock()
    self.modemReporter.browser.select_form.return_value = form_mock

    self.modemReporter.login()

    self.modemReporter.browser.open.assert_called_once_with(MODEM_ADDRESS)
    self.modemReporter.browser.select_form.assert_called_once()
    form_mock.set.assert_any_call('loginUsername', 'username')
    form_mock.set.assert_any_call('loginPassword', 'password') # nosec # noqa
    form_mock.choose_submit.assert_called_once()
    self.modemReporter.browser.submit_selected.assert_called_once()

  @patch('mysql.connector.connect')
  def test_report_events(self, connect_mock):
    EVENTS = [
      ['Wed Sep 09 11:00:00 2020', 'Error (4)', 'The description'],
      ['Thu Sep 10 09:00:00 2020', 'Error (4)', 'The description']
    ]
    SQL_QUERY = 'INSERT INTO `modem_events` (`description`, `priority`, `created_at`, `maintenance`) VALUES ("The description", 4, "2020-09-09 11:00:00", False), ("The description", 4, "2020-09-10 09:00:00", False)'
    cursor_mock = MagicMock()
    CONNECTION_MOCK.cursor.return_value = cursor_mock
    connect_mock.return_value = CONNECTION_MOCK

    self.modemReporter.report_events(EVENTS)

    connect_mock.assert_called_once()
    CONNECTION_MOCK.cursor.assert_called_once()
    cursor_mock.execute.assert_called_once_with(SQL_QUERY)
    CONNECTION_MOCK.commit.assert_called_once()
    cursor_mock.close.assert_called_once()
    CONNECTION_MOCK.close.assert_called_once()

  @freeze_time('2020-09-15 13:05:00')
  @patch('mysql.connector.connect')
  def test_report_events_when_no_times_have_been_established(self, connect_mock):
    EVENTS = [
      ['Time Not Established', 'Error (4)', 'The description'],
      ['Time Not Established', 'Error (4)', 'The description'],
      ['Time Not Established', 'Error (4)', 'The description']
    ]
    SQL_QUERY = 'INSERT INTO `modem_events` (`description`, `priority`, `created_at`, `maintenance`) VALUES ("The description", 4, "2020-09-15 13:05:00", False), ("The description", 4, "2020-09-15 13:05:00", False), ("The description", 4, "2020-09-15 13:05:00", False)'
    cursor_mock = MagicMock()
    CONNECTION_MOCK.cursor.return_value = cursor_mock
    connect_mock.return_value = CONNECTION_MOCK

    self.modemReporter.report_events(EVENTS)

    connect_mock.assert_called_once()
    CONNECTION_MOCK.cursor.assert_called_once()
    cursor_mock.execute.assert_called_once_with(SQL_QUERY)
    CONNECTION_MOCK.commit.assert_called_once()
    cursor_mock.close.assert_called_once()
    CONNECTION_MOCK.close.assert_called_once()

  @patch('mysql.connector.connect')
  def test_report_events_when_an_earlier_event_has_no_time_established(self, connect_mock):
    EVENTS = [
      ['Time Not Established', 'Error (4)', 'The description'],
      ['Wed Sep 09 11:00:00 2020', 'Error (4)', 'The description'],
      ['Thu Sep 10 09:00:00 2020', 'Error (4)', 'The description']
    ]
    SQL_QUERY = 'INSERT INTO `modem_events` (`description`, `priority`, `created_at`, `maintenance`) VALUES ("The description", 4, "2020-09-09 11:00:00", False), ("The description", 4, "2020-09-09 11:00:00", False), ("The description", 4, "2020-09-10 09:00:00", False)'
    cursor_mock = MagicMock()
    CONNECTION_MOCK.cursor.return_value = cursor_mock
    connect_mock.return_value = CONNECTION_MOCK

    self.modemReporter.report_events(EVENTS)

    connect_mock.assert_called_once()
    CONNECTION_MOCK.cursor.assert_called_once()
    cursor_mock.execute.assert_called_once_with(SQL_QUERY)
    CONNECTION_MOCK.commit.assert_called_once()
    cursor_mock.close.assert_called_once()
    CONNECTION_MOCK.close.assert_called_once()

  @patch('mysql.connector.connect')
  def test_report_events_when_a_later_event_has_no_time_established(self, connect_mock):
    EVENTS = [
      ['Wed Sep 09 11:00:00 2020', 'Error (4)', 'The description'],
      ['Thu Sep 10 09:00:00 2020', 'Error (4)', 'The description'],
      ['Time Not Established', 'Error (4)', 'The description']
    ]
    SQL_QUERY = 'INSERT INTO `modem_events` (`description`, `priority`, `created_at`, `maintenance`) VALUES ("The description", 4, "2020-09-09 11:00:00", False), ("The description", 4, "2020-09-10 09:00:00", False), ("The description", 4, "2020-09-10 09:00:00", False)'
    cursor_mock = MagicMock()
    CONNECTION_MOCK.cursor.return_value = cursor_mock
    connect_mock.return_value = CONNECTION_MOCK

    self.modemReporter.report_events(EVENTS)

    connect_mock.assert_called_once()
    CONNECTION_MOCK.cursor.assert_called_once()
    cursor_mock.execute.assert_called_once_with(SQL_QUERY)
    CONNECTION_MOCK.commit.assert_called_once()
    cursor_mock.close.assert_called_once()
    CONNECTION_MOCK.close.assert_called_once()

  @patch.object(ModemReporter, 'login')
  @patch.object(ModemReporter, 'logout')
  @patch.object(ModemReporter, 'report_events')
  @patch.object(ModemReporter, 'scrape_events')
  def test_run_when_enabled(self, login_mock, logout_mock, report_events_mock, scrape_events_mock):
    self.modemReporter.enabled = True
    self.modemReporter.run()

    login_mock.assert_called_once()
    scrape_events_mock.assert_called_once()
    report_events_mock.assert_called_once()
    logout_mock.assert_called_once()

  @patch.object(ModemReporter, 'login')
  @patch.object(ModemReporter, 'logout')
  @patch.object(ModemReporter, 'report_events')
  @patch.object(ModemReporter, 'scrape_events')
  def test_run_when_not_enabled(self, login_mock, logout_mock, report_events_mock, scrape_events_mock):
    self.modemReporter.enabled = False
    self.modemReporter.run()

    login_mock.assert_not_called()
    scrape_events_mock.assert_not_called()
    report_events_mock.assert_not_called()
    logout_mock.assert_not_called()

  def test_scrape_events(self):
    from bs4 import BeautifulSoup

    TABLE_ROWS_SOUP = """
    <tr><td></td><td></td><td></td></tr>
    <tr bgcolor="#EFEFEF"><td>Wed Sep 09 11:00:00 2020</td><td>Error (4)</td><td>The description</td></tr>
    <tr bgcolor="#EFEFEF"><td>Thu Sep 10 09:00:00 2020</td><td>Error (4)</td><td>The description</td></tr>
    <tr><td></td><td></td><td></td></tr>
    """
    EXPECTED_LOGS = [
      ['Wed Sep 09 11:00:00 2020', 'Error (4)', 'The description'],
      ['Thu Sep 10 09:00:00 2020', 'Error (4)', 'The description']
    ]


    page_mock = MagicMock()
    self.modemReporter.browser.get_current_page.return_value = page_mock
    page_mock.find.return_value = BeautifulSoup(TABLE_ROWS_SOUP, 'html.parser')

    self.assertEqual(
      self.modemReporter.scrape_events(),
      EXPECTED_LOGS
    )

    self.modemReporter.browser.open.assert_called_once_with(MODEM_ADDRESS + '/MotoSnmpLog.asp')
    page_mock.find.assert_called_once_with('table', class_='moto-table-content')

