import unittest
from freezegun import freeze_time
from unittest.mock import Mock, patch
from src.utils import calulate_percentage_lost, calculate_standard_deviation, get_addresses, get_downtime, ping_hosts

class TestUtilMethods(unittest.TestCase):
  @classmethod
  def setUpClass(self):
    from subprocess import CompletedProcess
    self.ping_args = ['ping', '-c', '5', '8.8.4.4']
    self.ping_response = CompletedProcess(args=self.ping_args, returncode=0, stdout=b'PING 8.8.4.4 (8.8.4.4): 56 data bytes\n64 bytes from 8.8.4.4: icmp_seq=0 ttl=53 time=33.309 ms\n64 bytes from 8.8.4.4: icmp_seq=1 ttl=53 time=31.647 ms\n64 bytes from 8.8.4.4: icmp_seq=2 ttl=53 time=35.030 ms\n64 bytes from 8.8.4.4: icmp_seq=3 ttl=53 time=35.696 ms\n64 bytes from 8.8.4.4: icmp_seq=4 ttl=53 time=33.078 ms\n\n--- 8.8.4.4 ping statistics ---\n5 packets transmitted, 5 packets received, 0.0% packet loss\nround-trip min/avg/max/stddev = 31.647/33.752/35.696/1.449 ms\n')

  def test_calculate_percentage_lost(self):
    self.assertEqual(
      calulate_percentage_lost([self.ping_response]),
      0.0
    )

  @patch('logging.Logger')
  def test_calculate_standard_deviation(self, mock_logger):
    self.assertEqual(
      calculate_standard_deviation([1,2,3,4,5], mock_logger),
      (3.0, 1.5811388300841898)
    )

    mock_logger.reset_mock()
    self.assertRaises(
      TypeError,
      calculate_standard_deviation,
      ([None, None, None, None], mock_logger)
    )

    mock_logger.reset_mock()
    calculate_standard_deviation([None, None, None, None], mock_logger)
    mock_logger.exception.assert_called_once()

  def test_get_addresses(self):
    self.assertEqual(get_addresses(''), [])
    self.assertEqual(get_addresses('8.8.4.4, 8.8.8.8'), ['8.8.4.4', '8.8.8.8'])
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
