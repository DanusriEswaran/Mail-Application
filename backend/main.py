from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import uvicorn
import os

app = FastAPI()

GMAIL_USER = os.environ.get("GMAIL_USER", "danuidentifier@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "hecs syke yjbv rpkg")


class EmailRequest(BaseModel):
    recipient_email: EmailStr
    subject: str
    body: str

@app.post("/send-email/")
async def send_email(email_request: EmailRequest):
    sender_email = GMAIL_USER
    sender_password = GMAIL_APP_PASSWORD
    recipient_email = email_request.recipient_email
    subject = email_request.subject
    body = email_request.body

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp: 
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        return {"message": "Email sent successfully!", "to": recipient_email, "subject": subject}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)