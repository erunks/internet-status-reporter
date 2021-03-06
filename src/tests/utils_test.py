import unittest
from freezegun import freeze_time
from unittest.mock import patch
from src.utils import calculate_percentage_lost, calculate_standard_deviation, format_modem_priority_as_int, format_modem_time_as_datetime, get_addresses, get_downtime, get_future_event_datetime, ping_hosts, remove_none

class TestUtilMethods(unittest.TestCase):
  @classmethod
  def setUpClass(self):
    from subprocess import CompletedProcess # nosec
    print('------------------------------ Utils Tests ------------------------------')
    self.ping_args = ['ping', '-c', '5', '8.8.4.4']
    self.ping_response = CompletedProcess(args=self.ping_args, returncode=0, stdout=b'PING 8.8.4.4 (8.8.4.4): 56 data bytes\n64 bytes from 8.8.4.4: icmp_seq=0 ttl=53 time=33.309 ms\n64 bytes from 8.8.4.4: icmp_seq=1 ttl=53 time=31.647 ms\n64 bytes from 8.8.4.4: icmp_seq=2 ttl=53 time=35.030 ms\n64 bytes from 8.8.4.4: icmp_seq=3 ttl=53 time=35.696 ms\n64 bytes from 8.8.4.4: icmp_seq=4 ttl=53 time=33.078 ms\n\n--- 8.8.4.4 ping statistics ---\n5 packets transmitted, 5 packets received, 0.0% packet loss\nround-trip min/avg/max/stddev = 31.647/33.752/35.696/1.449 ms\n')

  def test_calculate_percentage_lost(self):
    self.assertEqual(
      calculate_percentage_lost([self.ping_response]),
      0.0
    )

  @patch('logging.Logger')
  def test_calculate_standard_deviation_when_an_array_of_numbers_is_passed(self, mock_logger):
    self.assertEqual(
      calculate_standard_deviation([1,2,3,4,5], mock_logger),
      (3.0, 1.5811388300841898)
    )

  @patch('logging.Logger')
  def test_calculate_standard_deviation_when_an_array_of_one_number_is_passed(self, mock_logger):
    self.assertEqual(
      calculate_standard_deviation([1.0], mock_logger),
      (1.0, 0)
    )

  @patch('logging.Logger')
  def test_calculate_standard_deviation_when_an_empty_array_is_passed(self, mock_logger):
    self.assertEqual(
      calculate_standard_deviation([], mock_logger),
      None
    )

  # These two tests might not be the best, since we should never expect strings to be passed
  # here, but we do still want to check the TypeError is raised and the exception is logged.
  # The strings will help trigger those.
  @patch('logging.Logger')
  def test_calculate_standard_deviation_when_a_TypeError_is_raised(self, mock_logger):
    self.assertRaises(
      TypeError,
      calculate_standard_deviation(["String", 1.0, 2.0, 3.0], mock_logger)
    )

  @patch('logging.Logger')
  def test_calculate_standard_deviation_when_an_exception_is_logged(self, mock_logger):
    calculate_standard_deviation(["some", "string", "right", "here"], mock_logger)
    mock_logger.exception.assert_called_once()

  def test_format_modem_priority_as_int(self):
    self.assertEqual(format_modem_priority_as_int('Error (4)'), 4)

  def test_format_modem_time_as_datetime(self):
    from datetime import datetime
    modem_time_datetime = datetime(2020,9,9,11,10,37)

    self.assertEqual(
      format_modem_time_as_datetime('Wed Sep 09 11:10:37 2020'),
      modem_time_datetime
    )

  def test_get_addresses_when_passed_an_empty_array(self):
    self.assertEqual(get_addresses(''), [])

  def test_get_addresses_when_passed_an_array_of_ip_addresses(self):
    self.assertEqual(get_addresses('8.8.4.4, 8.8.8.8'), ['8.8.4.4', '8.8.8.8'])

  def test_get_addresses_when_passed_an_array_of_url_addresses(self):
    self.assertEqual(get_addresses('google.com, youtube.com'), ['google.com', 'youtube.com'])

  @freeze_time('2020-06-08 13:05:00')
  def test_get_downtime(self):
    from datetime import datetime
    last_issue_at = datetime(2020,6,8,13,0)

    self.assertEqual(get_downtime(last_issue_at), '0:05:00')

  def test_get_future_event_datetime_when_there_is_a_future_datetime(self):
    from datetime import datetime

    FUTURE_EVENT_LOGS = [
      ['Time Not Established', 4, "This was the last description"],
      ['Time Not Established', 4, "This isn't the last description"],
      ['Wed Sep 16 09:00:00 2020', 4, "This is now the last description"]
    ]

    self.assertEqual(
      get_future_event_datetime(FUTURE_EVENT_LOGS, 0),
      datetime(2020, 9, 16, 9, 0, 0)
    )

  @freeze_time('2020-09-15 13:05:00')
  def test_get_future_event_datetime_when_there_is_no_future_datetime(self):
    from datetime import datetime

    FUTURE_EVENT_LOGS = [
      ['Time Not Established', 4, "This was the last description"],
      ['Time Not Established', 4, "This isn't the last description"],
      ['Time Not Established', 4, "This is now the last description"]
    ]

    self.assertEqual(
      get_future_event_datetime(FUTURE_EVENT_LOGS, 0),
      datetime(2020, 9, 15, 13, 5, 0)
    )

  @patch('subprocess.run')
  def test_ping_hosts(self, mock_run):
    from subprocess import PIPE # nosec
    mock_run.return_value = self.ping_response

    self.assertListEqual(ping_hosts(['8.8.4.4'], 5), [self.ping_response])
    mock_run.assert_called_with(self.ping_args, stdout=PIPE)

  def test_remove_none_when_passed_an_array_of_none(self):
    self.assertEqual(remove_none([None,None,None,None]),[])

  def test_remove_none_when_passed_an_array_containing_none(self):
    self.assertEqual(remove_none([1,None,"Something",420.69]),[1, "Something", 420.69])
