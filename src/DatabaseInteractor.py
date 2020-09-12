from sys import exc_info
from src.MailLogger import MailLogger

class DatabaseInteractor(MailLogger):
  def __init__(self):
    from dotenv import load_dotenv, find_dotenv

    super().__init__()
    load_dotenv(find_dotenv())

    self.connection = None

  def __del__(self):
    self.disconnect_database()
  
  def connect_database(self):
    from mysql.connector import Error as DB_Error, ProgrammingError, connect, errorcode
    from os import getenv

    try:
      self.connection = connect(
        database = getenv('DATABASE'),
        host = getenv('DB_HOST'),
        password = getenv('DB_PASSWORD'),
        user = getenv('DB_USERNAME')
      )

    except ProgrammingError as err:
      if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        self.logger.error(f'Access denied: {err}')
      else:
        self.logger.exception(f'Unexpected error: {err}')
    except DB_Error as err:
      if err.errno == errorcode.ER_BAD_DB_ERROR:
        self.logger.error(f'Database does not exist: {err}')
      else:
        self.logger.exception(f'Unexpected error: {err}')
    except:
      self.logger.exception(f'Unexpected error: {exc_info()[0]}')

  def disconnect_database(self):
    if self.connection != None:
      self.connection.close()
      self.connection = None

  def execute_sql(self, sql, values):
    from mysql.connector import Error as DB_Error, ProgrammingError, errorcode

    try:
      cursor = self.connection.cursor()
      cursor.execute(sql, values)
      self.connection.commit()
      cursor.close()

    except:
      self.logger.exception(f'Unexpected error: {exc_info()[0]}')