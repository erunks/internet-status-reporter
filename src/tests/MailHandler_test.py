import re
import unittest
from unittest.mock import MagicMock, Mock, patch
from src.MailHandler import MailHandler

class TestMailHandler(unittest.TestCase):
  @classmethod
  def setUpClass(self):
    print('------------------------------ MailHandler Tests ------------------------------')
    self.sender = 'pi@gmail.com'
    self.receiver = 'receiver@gmail.com'
    self.subject = 'Internet Status Reporter: ERROR!'
    self.username = self.sender
    self.password = 'pi_email_password'
    self.handler = MailHandler(
      ('smtp.gmail.com', 587),
      self.sender,
      self.receiver,
      self.subject,
      (self.username, self.password)
    )

  def test_create_message(self):
    message_body = 'Testing MailHandler.__create_message'
    message = self.handler._MailHandler__create_message(
      self.sender,
      self.receiver,
      self.subject,
      message_body
    )
    regexes = {
      'Subject': [r'Subject:\s(.+)\nFrom', self.subject],
      'From': [r'From:\s((\w+([@.])?){3})', self.sender],
      'To': [r'To:\s((\w+([@.])?){3})', self.receiver],
      'Body': [r'Content-Transfer-Encoding: 7bit\n\n(.+)\n--', message_body]
    }

    for key in regexes:
      match = re.search(regexes[key][0], message)
      self.assertEqual(match.group(1), regexes[key][1])


  @patch('smtplib.SMTP')
  @patch('ssl.create_default_context')
  def test_emit(self, ssl_context_mock, smtp_mock):
    record = MagicMock()
    record.exc_text.return_value = 'Exc_text'
    record.payload.return_value = 'Payload'

    smtp_instance_mock = MagicMock()
    smtp_mock.return_value = smtp_instance_mock

    create_message_mock = MagicMock()
    create_message_mock.return_value = 'Some messsage'
    self.handler._MailHandler__create_message = create_message_mock

    self.handler.emit(record)
    smtp_mock.assert_called_once_with(
      'smtp.gmail.com',
      587
    )
    ssl_context_mock.assert_called_once()
    create_message_mock.assert_called_once()
    self.assertEqual(smtp_instance_mock.ehlo.call_count, 2)
    smtp_instance_mock.starttls.assert_called_once()
    smtp_instance_mock.login.assert_called_once()
    smtp_instance_mock.sendmail.assert_called_once_with(
      self.sender,
      [self.receiver],
      create_message_mock.return_value
    )
    smtp_instance_mock.quit.assert_called_once()
