import unittest
from freezegun import freeze_time
from unittest.mock import Mock, patch
from src.utils import calculate_percentage_lost, calculate_standard_deviation, get_addresses, get_downtime, ping_hosts, remove_none

class TestUtilMethods(unittest.TestCase):
  @classmethod
  def setUpClass(self):
    from subprocess import CompletedProcess
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
  def test_calculate_standard_deviation_when_an_array_of_numbers_and_none_is_passed(self, mock_logger):
    self.assertEqual(
      calculate_standard_deviation([None,1.0,2,3,None,4.0,5], mock_logger),
      (3.0, 1.5811388300841898)
    )

  @patch('logging.Logger')
  def test_calculate_standard_deviation_when_an_array_of_one_number_and_none_is_passed(self, mock_logger):
    self.assertEqual(
      calculate_standard_deviation([None,1.0,None], mock_logger),
      (1.0, 0)
    )

  @patch('logging.Logger')
  def test_calculate_standard_deviation_when_an_array_of_none_is_passed(self, mock_logger):
    self.assertEqual(
      calculate_standard_deviation([None, None, None, None], mock_logger),
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

  @patch('subprocess.run')
  def test_ping_hosts(self, mock_run):
    from subprocess import PIPE
    mock_run.return_value = self.ping_response

    self.assertListEqual(ping_hosts(['8.8.4.4'], 5), [self.ping_response])
    mock_run.assert_called_with(self.ping_args, stdout=PIPE)

  def test_remove_none_when_passed_an_array_of_none(self):
    self.assertEqual(remove_none([None,None,None,None]),[])

  def test_remove_none_when_passed_an_array_containing_none(self):
    self.assertEqual(remove_none([1,None,"Something",420.69]),[1, "Something", 420.69])