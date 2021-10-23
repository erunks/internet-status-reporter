class MailLogger:
  def __init__(self):
    from logging import ERROR, INFO, basicConfig, getLogger, Formatter
    from src.MailHandler import MailHandler
    from os import getenv

    logFormat = '%(asctime)s - %(levelname)s: %(message)s'
    basicConfig(
      filename=getenv('LOG_FILE'),
      filemode='a',
      format=logFormat,
      level=INFO
    )

    mailHandler = MailHandler(
      (getenv('SMTP_SERVER'), getenv('SMTP_PORT')),
      getenv('PI_EMAIL'),
      getenv('MAILTO').split(','),
      'Internet Status Reporter: ERROR!',
      (getenv('PI_EMAIL'), getenv('PI_EMAIL_PASSWORD'))
    )
    mailHandler.setLevel(ERROR)
    mailHandler.setFormatter(Formatter(logFormat))

    self.logger = getLogger('%s_Logger' % self.__class__.__name__)
    self.logger.addHandler(mailHandler)
    self.logger.info('%s is starting up' % self.__class__.__name__)
