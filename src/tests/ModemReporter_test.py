import unittest
from mysql.connector import Error as DB_Error, ProgrammingError, errorcode
from os import getenv
from unittest.mock import MagicMock, patch
from src.ModemReporter import ModemReporter

class TestModemReporter(unittest.TestCase):
  @classmethod
  def setUpClass(self):
    self.modemReporter = ModemReporter()
    self.modemReporter.connection = MagicMock()
    self.modemReporter.logger = MagicMock()
