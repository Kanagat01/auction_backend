import datetime
import os

from fastapi import FastAPI
from pydantic import BaseModel
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = FastAPI()
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_SERVER_SECRET = os.environ.get('EMAIL_SERVER_SECRET')


# print('-------------------------------')
# print('USER:', EMAIL_HOST_USER)
# print('PASS:', EMAIL_HOST_PASSWORD)
# print('SECRET:', EMAIL_SERVER_SECRET)
# print('-------------------------------')


class Item(BaseModel):
    to_who: str
    subject: str
    description: str
    email_secret: str


@app.post("/send_email/")
async def send_email(item: Item):
    if item.email_secret != EMAIL_SERVER_SECRET:
        return {'info': 'denied'}

    recipients = item.to_who.split(', ')
    msg = MIMEMultipart()
    msg['From'] = EMAIL_HOST_USER
    msg['Subject'] = item.subject
    msg.attach(MIMEText(item.description, 'plain'))
    from datetime import datetime

    print(f'------------{datetime.utcnow()}-------------')
    print('EMAIL_HOST_USER:', EMAIL_HOST_USER)
    print('email:', item.to_who)
    print('subject:', item.subject)
    print('---------------------------------------')

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
    server.sendmail(msg['From'], [recipients[0]] + ['BCC: ' + rec for rec in recipients[1:]], msg.as_string())
    # server.sendmail(msg['From'], msg['To'].split(', '), msg.as_string())
    server.quit()

    return {"info": "Successfully sent email to " + item.to_who}
