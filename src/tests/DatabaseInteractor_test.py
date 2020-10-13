import unittest
from dotenv import load_dotenv, find_dotenv
from mysql.connector import Error as DB_Error, ProgrammingError, errorcode
from unittest.mock import MagicMock, patch
from src.DatabaseInteractor import DatabaseInteractor

load_dotenv(find_dotenv(".env.test"), override=True)

SQL = 'sql string'
VALUES = (1, 2, True)

CONNECTION_MOCK = MagicMock()

class TestDatabaseInteractor(unittest.TestCase):
  @classmethod
  def setUpClass(self):
    print('------------------------------ DatabaseInteractor Tests ------------------------------')
    self.databseInteractor = DatabaseInteractor()
    self.databseInteractor.logger = MagicMock()

  @classmethod
  def resetMocks(self):
    CONNECTION_MOCK.reset_mock(return_value=True, side_effect=True)
    CONNECTION_MOCK.cursor.side_effect = None
    CONNECTION_MOCK.cursor.return_value = None
    self.databseInteractor.logger.reset_mock()

  @patch('mysql.connector.connect', return_value=CONNECTION_MOCK)
  def test_connect_database(self, connect_mock):
    self.assertEqual(self.databseInteractor.connection, None)

    self.databseInteractor.connect_database()

    connect_mock.assert_called_once_with( # nosec
      database = 'database',
      host = 'host',
      password = 'password', # nosec # noqa
      user = 'username'
    )

    self.assertEqual(self.databseInteractor.connection, CONNECTION_MOCK)

  @patch('mysql.connector.connect', side_effect=ProgrammingError(errno=errorcode.ER_ACCESS_DENIED_ERROR))
  def test_connect_database_when_access_denied(self, _connect_mock):
    self.resetMocks()

    self.databseInteractor.connect_database()
    self.databseInteractor.logger.error.assert_called_once()

  @patch('mysql.connector.connect', side_effect=DB_Error(errno=errorcode.ER_BAD_DB_ERROR))
  def test_connect_database_when_database_does_not_exist(self, _connect_mock):
    self.resetMocks()

    self.databseInteractor.connect_database()
    self.databseInteractor.logger.error.assert_called_once()

  @patch('mysql.connector.connect', side_effect=Exception())
  def test_connect_database_when_unexpected_error(self, _connect_mock):
    self.resetMocks()

    self.databseInteractor.connect_database()
    self.databseInteractor.logger.exception.assert_called_once()

  def test_disconnect_database_when_there_is_an_active_connection(self):
    self.resetMocks()

    self.databseInteractor.connection = CONNECTION_MOCK
    self.databseInteractor.disconnect_database()
    CONNECTION_MOCK.close.assert_called_once()

  def test_disconnect_database_when_there_is_no_active_connection(self):
    self.resetMocks()

    self.databseInteractor.connection = None
    self.databseInteractor.disconnect_database()
    CONNECTION_MOCK.close.assert_not_called()

  def test_execute_sql_and_get_results(self):
    self.resetMocks()
    self.databseInteractor.connection = CONNECTION_MOCK

    cursor_mock = MagicMock()
    cursor_mock.fetchall.return_value = "results"
    CONNECTION_MOCK.cursor.return_value = cursor_mock

    self.assertEqual(
      self.databseInteractor.execute_sql_and_get_results(SQL, VALUES),
      "results"
    )

    self.databseInteractor.connection.cursor.assert_called_once()
    cursor_mock.execute.assert_called_once_with(SQL, VALUES)
    cursor_mock.fetchall.assert_called_once()
    cursor_mock.close.assert_called_once()

  def test_execute_sql_and_get_results_and_an_unexpected_error_is_raised(self):
    self.resetMocks()
    self.databseInteractor.connection = CONNECTION_MOCK

    CONNECTION_MOCK.cursor.side_effect = Exception()

    self.databseInteractor.execute_sql_and_get_results(SQL, VALUES)
    self.databseInteractor.logger.exception.assert_called_once()

  def test_execute_sql_with_commit(self):
    self.resetMocks()
    self.databseInteractor.connection = CONNECTION_MOCK

    cursor_mock = MagicMock()
    CONNECTION_MOCK.cursor.return_value = cursor_mock

    self.databseInteractor.execute_sql_with_commit(SQL, VALUES)

    self.databseInteractor.connection.cursor.assert_called_once()
    cursor_mock.execute.assert_called_once_with(SQL, VALUES)
    self.databseInteractor.connection.commit.assert_called_once()
    cursor_mock.close.assert_called_once()

  def test_execute_sql_with_commit_and_an_unexpected_error_is_raised(self):
    self.resetMocks()
    self.databseInteractor.connection = CONNECTION_MOCK

    CONNECTION_MOCK.cursor.side_effect = Exception()

    self.databseInteractor.execute_sql_with_commit(SQL, VALUES)
    self.databseInteractor.logger.exception.assert_called_once()