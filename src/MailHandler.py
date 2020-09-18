from logging.handlers import SMTPHandler

class MailHandler(SMTPHandler):
  def __create_message(self, from_addr, to_addr, message_subject, message_body):
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    message = MIMEMultipart('alternative')
    message['Subject'] = message_subject
    message['From'] = from_addr
    message['To'] = to_addr
    message.attach(MIMEText(message_body, 'plain'))
    return message.as_string()

  def emit(self, record):
    try:
      import string
      from smtplib import SMTP, SMTP_PORT
      from ssl import create_default_context

      port = self.mailport
      if not port:
        port = SMTP_PORT

      smtp = SMTP(self.mailhost, port)
      context = create_default_context()
      message = self.__create_message(
        self.fromaddr,
        ' , '.join(self.toaddrs),
        self.getSubject(record),
        self.format(record)
      )

      if self.username:
        smtp.ehlo()
        smtp.starttls(context=context)
        smtp.ehlo()
        smtp.login(self.username, self.password)

      smtp.sendmail(self.fromaddr, self.toaddrs, message)
      smtp.quit()

    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        self.handleError(record)
