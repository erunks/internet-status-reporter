import unittest
from unittest.mock import MagicMock, patch
from src.MailLogger import MailLogger

class TestMailLogger(unittest.TestCase):
  @patch('logging.getLogger')
  @patch('src.MailHandler.MailHandler')
  def test_mail_logger_initializes_correctly(self, mail_handler_mock, get_logger_mock):
    mail_handler_instance_mock = MagicMock()
    mail_handler_mock.return_value = mail_handler_instance_mock

    logger_mock = MagicMock()
    get_logger_mock.return_value = logger_mock

    MailLogger()

    mail_handler_instance_mock.setLevel.assert_called_once()
    mail_handler_instance_mock.setFormatter.assert_called_once()
    get_logger_mock.assert_called_once_with('MailLogger_Logger')
    logger_mock.addHandler.assert_called_once_with(mail_handler_instance_mock)
    logger_mock.info.assert_called_once_with('MailLogger is starting up')
