import unittest
from dotenv import load_dotenv, find_dotenv
from freezegun import freeze_time
from unittest.mock import MagicMock, patch
from src.InternetStatusReporter import InternetStatusReporter

load_dotenv(find_dotenv(".env.test"), override=True)
class TestInternetStatusReporter(unittest.TestCase):
  @classmethod
  def setUpClass(self):
    print('------------------------------ InternetStatusReporter Tests ------------------------------')
    self.reporter = InternetStatusReporter()
    self.reporter.lock = MagicMock()
    self.reporter.logger = MagicMock()
    self.reporter.modemReporter = MagicMock()

  def setUp(self):
    self.resetMocks()

  @classmethod
  def resetMocks(self):
    self.reporter.lock.reset_mock()
    self.reporter.logger.reset_mock()
    self.reporter.modemReporter.reset_mock()

  def test_is_down_when_current_status_is_normal(self):
    self.reporter.current_status = self.reporter.NETWORK_STATUS['NORMAL']
    self.assertFalse(self.reporter._InternetStatusReporter__is_down())

  def test_is_down_when_current_status_is_degraded(self):
    self.reporter.current_status = self.reporter.NETWORK_STATUS['DEGRADED']
    self.assertTrue(self.reporter._InternetStatusReporter__is_down())

  def test_is_down_when_current_status_is_down(self):
    self.reporter.current_status = self.reporter.NETWORK_STATUS['DOWN']
    self.assertTrue(self.reporter._InternetStatusReporter__is_down())

  @patch('src.utils.ping_hosts')
  @patch('src.utils.calculate_percentage_lost')
  def test_check_status(self, calculate_percentage_lost_mock, ping_hosts_mock):
    loss = 0.0
    calculate_percentage_lost_mock.return_value = loss
    self.assertEqual(self.reporter.check_status(), loss)
    ping_hosts_mock.assert_called_once()
    calculate_percentage_lost_mock.assert_called_once()
  
  def test_update_status_when_current_status_is_normal_and_loss_is_zero(self):
    normal_status = self.reporter.NETWORK_STATUS['NORMAL']
    self.reporter.current_status = normal_status
    self.reporter.update_status(0.0)
    self.assertEqual(self.reporter.current_status, normal_status)

  @patch('datetime.datetime')
  def test_update_status_when_current_status_is_normal_and_loss_is_not_zero(self, datetime_mock):
    normal_status = self.reporter.NETWORK_STATUS['NORMAL']
    self.reporter.current_status = normal_status
    self.reporter.update_status(0.1)
    self.assertNotEqual(self.reporter.current_status, normal_status)
    self.assertEqual(self.reporter.current_status, self.reporter.NETWORK_STATUS['DEGRADED'])
    self.reporter.logger.warning.assert_called_once()
    datetime_mock.now.assert_called_once()

  @patch('datetime.datetime')
  def test_update_status_when_current_status_is_normal_and_loss_is_max(self, datetime_mock):
    normal_status = self.reporter.NETWORK_STATUS['NORMAL']
    self.reporter.current_status = normal_status
    self.reporter.update_status(100.0)
    self.assertNotEqual(self.reporter.current_status, normal_status)
    self.assertEqual(self.reporter.current_status, self.reporter.NETWORK_STATUS['DOWN'])
    self.reporter.logger.warning.assert_called_once()
    datetime_mock.now.assert_called_once()

  def test_update_status_when_current_status_is_not_normal_and_loss_is_zero(self):
    self.reporter.current_status = self.reporter.NETWORK_STATUS['DOWN']
    self.reporter.update_status(0.0)
    self.assertEqual(self.reporter.current_status, self.reporter.NETWORK_STATUS['NORMAL'])
    self.reporter.logger.info.assert_called_once()
    self.reporter.modemReporter.run.assert_called_once()
    self.reporter.lock.release.assert_called_once()

  @patch('os.getenv')
  @patch('tcp_latency.measure_latency')
  def test_measure_latency(self, measure_latency_mock, getenv_mock):
    self.reporter.latency_addresses = ['google.com']
    getenv_mock.return_value = 10
    measure_latency_mock.return_value = [3.97, 3.81, 4.56, 4.33, 3.97, 8.9, 4.83, 4.07, 4.19, 5.93]

    self.assertEqual(
      self.reporter.measure_latency(),
      '{"google.com": {"deviation": 1.5491158768794542, "max": 8.9, "mean": 4.856, "min": 3.81}}'
    )

  @freeze_time('2020-06-08 13:05:00')
  def test_report_issue(self):
    from datetime import datetime
    self.reporter.last_issue_at = datetime(2020,6,8,13,0) 
    loss = 42.0
    info = ''

    # Probably a better way to handle mocking this:
    self.reporter.connect_database = MagicMock()
    self.reporter.execute_sql_with_commit = MagicMock()
    self.reporter.disconnect_database = MagicMock()

    self.reporter.report_issue(loss, info)

    self.reporter.connect_database.assert_called_once()
    self.reporter.execute_sql_with_commit.assert_called_once_with(
      'INSERT INTO `outtages` (`loss`, `downtime`, `created_at`, `maintenance`, `info`) VALUES (%s, %s, %s, %s, %s)',
      (loss, '0:05:00', datetime.now(), False, info)
    )
    self.reporter.disconnect_database.assert_called_once()
