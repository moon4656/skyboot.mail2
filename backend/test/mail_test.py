import smtplib
from email.mime.text import MIMEText

def send_mail():
    msg = MIMEText("테스트 메일")
    msg["Subject"] = "FastAPI -> Gmail Relay Test"
    msg["From"] = "moon4656@skyboot.co.kr"
    msg["To"] = "moon4656@gmail.com"

    with smtplib.SMTP("localhost") as server:  # FastAPI → Postfix(localhost)
        server.sendmail(msg["From"], [msg["To"]], msg.as_string())

send_mail()
