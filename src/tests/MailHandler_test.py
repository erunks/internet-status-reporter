import re
import unittest
from unittest.mock import Mock, patch
from src.MailHandler import MailHandler

class TestMailHandler(unittest.TestCase):
  @classmethod
  def setUpClass(self):
    self.sender = 'pi@gmail.com'
    self.receiver = 'receiver@gmail.com'
    self.subject = 'Internet Status Reporter: ERROR!'
    self.handler = MailHandler(
      ('smtp.gmail.com', 587),
      self.sender,
      self.receiver,
      self.subject,
      (self.sender, 'pi_email_password')
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
      "Subject": [r"Subject:\s(.+)\nFrom", self.subject],
      "From": [r"From:\s((\w+([@.])?){3})", self.sender],
      "To": [r"To:\s((\w+([@.])?){3})", self.receiver],
      "Body": [r"Content-Transfer-Encoding: 7bit\n\n(.+)\n--", message_body]
    }

    for key in regexes:
      match = re.search(regexes[key][0], message)
      self.assertEqual(match.group(1), regexes[key][1])


  def test_emit(self):
    self.assertTrue(True)
