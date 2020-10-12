import unittest
from unittest.mock import MagicMock, patch
from src.MailLogger import MailLogger

class TestMailLogger(unittest.TestCase):
  @classmethod
  def setUpClass(self):
    print('------------------------------ MailLogger Tests ------------------------------')
    self.logger = MagicMock()
    self.mail_handler = MagicMock()

  @patch('logging.getLogger')
  @patch('src.MailHandler.MailHandler')
  def test_mail_logger_initializes_correctly(self, mail_handler_mock, get_logger_mock):
    mail_handler_mock.return_value = self.mail_handler
    get_logger_mock.return_value = self.logger

    MailLogger()

    self.mail_handler.setLevel.assert_called_once()
    self.mail_handler.setFormatter.assert_called_once()
    get_logger_mock.assert_called_once_with('MailLogger_Logger')
    self.logger.addHandler.assert_called_once_with(self.mail_handler)
    self.logger.info.assert_called_once_with('MailLogger is starting up')
