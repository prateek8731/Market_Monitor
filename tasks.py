import requests, os, smtplib, time
from email.message import EmailMessage

def send_webhook_alert(url, payload):
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code, r.text
    except Exception as e:
        return None, str(e)

def send_email_alert(to_email, subject, body):
    host = os.getenv("SMTP_HOST","")
    port = int(os.getenv("SMTP_PORT","587") or 587)
    user = os.getenv("SMTP_USER","")
    pwd = os.getenv("SMTP_PASS","")
    if not host or not user or not pwd:
        return {"error":"SMTP not configured"}
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = user
        msg["To"] = to_email
        msg.set_content(body)
        with smtplib.SMTP(host, port, timeout=10) as s:
            s.starttls()
            s.login(user, pwd)
            s.send_message(msg)
        return {"ok":True}
    except Exception as e:
        return {"error":str(e)}

def send_sms_alert(phone, message):
    sid = os.getenv("TWILIO_SID","")
    token = os.getenv("TWILIO_TOKEN","")
    from_num = os.getenv("TWILIO_FROM","")
    if not sid or not token or not from_num:
        return {"error":"Twilio not configured"}
    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
        data = {"From": from_num, "To": phone, "Body": message}
        r = requests.post(url, data=data, auth=(sid, token), timeout=10)
        return {"status": r.status_code}
    except Exception as e:
        return {"error":str(e)}

def retrain_and_save_model(example_ticker="AAPL", days=1000):
    try:
        from data_feed import DataFeed
        from models.classifier_model import ClassifierModel
        df = DataFeed()
        hist = df.get_historical(example_ticker, provider="AlphaVantage", days=days)
        clf = ClassifierModel()
        metrics = clf.train(hist, horizon=3, ret_thresh=0.01)
        return "classifier_model.pkl"
    except Exception as e:
        return str(e)