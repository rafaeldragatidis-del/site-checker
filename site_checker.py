import smtplib
import requests
import os
from email.message import EmailMessage

# Ανάκτηση δεδομένων από τα GitHub Secrets
EMAIL_SENDER = os.environ.get('EMAIL_SENDER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')

def send_email(target_email, url):
    msg = EmailMessage()
    msg['Subject'] = 'Ειδοποίηση Ασφαλείας για το site σας'
    msg['From'] = EMAIL_SENDER
    msg['To'] = target_email
    msg.set_content(f"Γεια σας, ελέγξαμε το site {url} και βρήκαμε κενά ασφαλείας.")
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)

def check_sites():
    if not os.path.exists('sites.txt'):
        print("Το αρχείο sites.txt δεν βρέθηκε.")
        return

    with open('sites.txt', 'r') as f:
        for line in f:
            if not line.strip(): continue
            url, email = line.strip().split(',')
            
            try:
                print(f"Ελέγχω το: {url}")
                response = requests.get(url, timeout=10)
                # Έλεγχος για κενά ασφαλείας
                if 'Content-Security-Policy' not in response.headers:
                    print(f"Βρέθηκε κενό! Αποστολή στο {email}")
                    send_email(email, url)
            except Exception as e:
                print(f"Σφάλμα στο {url}: {e}")

if __name__ == "__main__":
    check_sites()
