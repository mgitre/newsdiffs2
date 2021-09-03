import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import yaml


class CustomEmail:
    def __init__(self):
        self.content = ""
        self.empty = True
        with open("config.yaml") as f:
            config = yaml.safe_load(f)['EMAIL']
        self.sender_email = config['USER']
        self.receiver_email = config['RECEIVER_EMAIL']
        self.password = config['PASSWORD']
        self.smtp_server = config['SMTP_SERVER']
        self.smtp_port = config['SMTP_PORT']

    def addHeader(self, header):
        self.content += "<h2>{}</h2><br>".format(header)

    def addArticle(self, changed):
        self.empty = False
        (name, url, headline, times) = changed
        self.content += "<a href=\"{url}\">{headline}</a> has now been <a href=\"{changedurl}\">changed</a> {times} time(s). <br><br>".format(
            url=url, headline=headline, times=times - 1, changedurl="http://192.168.1.10:3301/" + name + "/" + url)

    def send(self):
        message = MIMEMultipart("alternative")
        message["Subject"] = "NewsDiffs update!"
        message["From"] = self.sender_email
        message["To"] = self.receiver_email
        html = MIMEText(self.content, "html")
        message.attach(html)
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
            server.login(self.sender_email, self.password)
            server.sendmail(
                self.sender_email, self.receiver_email, message.as_string()
            )
