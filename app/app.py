import email
import imaplib
import logging
import os
import poplib
import re
import time
from email.header import decode_header
import my_logging_module as sn

import psycopg2
from dotenv import load_dotenv

# Logging configuration
# Configure logging to both console and file
# logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
# rootLogger = logging.getLogger()
# rootLogger.setLevel(logging.INFO)

# # fileHandler = logging.FileHandler("{0}/{1}.log".format(logPath, fileName))
# # fileHandler.setFormatter(logFormatter)
# # rootLogger.addHandler(fileHandler)

# consoleHandler = logging.StreamHandler()
# consoleHandler.setFormatter(logFormatter)
# rootLogger.addHandler(consoleHandler)

logging = sn.sane_logger

# Load environment variables from the .env file
load_dotenv()

# Database configuration - using environment variables for sensitive data
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'user'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'database': os.getenv('DB_NAME', 'email_db'),
    'port': os.getenv('DB_PORT', 5432)  # Default PostgreSQL port
}

# IMAP/POP3 Mailbox configuration
mail_config = {
    'imap_host': os.getenv('IMAP_HOST', 'imap.mailserver.com'),
    'pop_host': os.getenv('POP_HOST', 'pop.mailserver.com'),
    'username': os.getenv('MAIL_USERNAME', 'your-email@mail.com'),
    'password': os.getenv('MAIL_PASSWORD', 'your-password'),
    'protocol': os.getenv('MAIL_PROTOCOL', 'imap')  # Set default to 'imap'
}

# Helper function to sanitize strings
def sanitize_string(input_string):
    return re.sub(r'[^\x20-\x7E]', '', input_string).strip()

# Input Validation Function
def validate_email_data(subject, sender, content):
    if not subject or len(subject) > 255:
        raise ValueError("Invalid subject: Subject is either empty or too long.")
    if not sender or len(sender) > 255 or not re.match(r"[^@]+@[^@]+\.[^@]+", sender):
        raise ValueError("Invalid sender: Sender is either empty, too long, or not a valid email address.")
    if not content or len(content) > 5000:
        raise ValueError("Invalid content: Email content is either empty or too long.")
    return True

# Connect to the PostgreSQL database
def connect_db():
    try:
        connection = psycopg2.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password'],
            dbname=db_config['database'],
            port=db_config['port']
        )
        return connection
    except psycopg2.Error as err:
        logging.error(f"Error connecting to the database: {err}")
        raise

# Save email to the database
def save_email_to_db(subject, sender, content):
    try:
        # Sanitize inputs
        subject = sanitize_string(subject)
        sender = sanitize_string(sender)
        content = sanitize_string(content)

        # Validate inputs
        validate_email_data(subject, sender, content)

        # Database connection
        db = connect_db()
        cursor = db.cursor()

        # Create table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id SERIAL PRIMARY KEY,
            subject TEXT NOT NULL,
            sender TEXT NOT NULL,
            body TEXT NOT NULL,
            processed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        query = "INSERT INTO emails (subject, sender, body, processed) VALUES (%s, %s, %s, %s)"
        values = (subject, sender, content, False)

        cursor.execute(query, values)
        db.commit()

        cursor.close()
        db.close()
        logging.info(f"Email saved: Subject: {subject}, Sender: {sender}")
    except psycopg2.Error as err:
        logging.error(f"Database error: {err}")
        db.rollback()
    except ValueError as val_err:
        logging.error(f"Validation error: {val_err}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

# Fetch new emails using IMAP
def fetch_emails_imap():
    try:
        imap = imaplib.IMAP4_SSL(mail_config['imap_host'])
        imap.login(mail_config['username'], mail_config['password'])

        # Select the mailbox you want to check (INBOX by default)
        imap.select('inbox')

        # Search for all unseen (unread) emails
        status, messages = imap.search(None, '(UNSEEN)')
        email_ids = messages[0].split()
        logging.info(f"Found {len(email_ids)} new emails")

        for email_id in email_ids:
            logging.info(f"Fetching email-id: {email_id.decode('utf-8')}")
            status, msg_data = imap.fetch(email_id, '(RFC822)')
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Decode email subject
            subject, encoding = decode_header(msg['Subject'])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or 'utf-8')

            # Get email sender
            sender = msg.get('From')

            # Extract email body (text/plain content)
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == 'text/plain':
                        content = part.get_payload(decode=True).decode('utf-8')
                        save_email_to_db(subject, sender, content)
            else:
                content = msg.get_payload(decode=True).decode('utf-8')
                logging.info(f"Email from: {msg.get('From')}, Subject: {subject[:50]}..., Content: {content[:100]}...")
                save_email_to_db(subject, sender, content)

        imap.logout()
    except Exception as e:
        logging.error(f"Error fetching emails via IMAP: {e}")

# Fetch new emails using POP3
def fetch_emails_pop3():
    try:
        pop_conn = poplib.POP3_SSL(mail_config['pop_host'])
        pop_conn.user(mail_config['username'])
        pop_conn.pass_(mail_config['password'])

        # Get message count
        num_messages = len(pop_conn.list()[1])
        logging.info(f"Found {num_messages} new emails")

        for i in range(num_messages):
            logging.info(f"Fetching email-id: {i+1}/{num_messages}")
            # Fetch the email message by its index
            raw_email = b'\n'.join(pop_conn.retr(i+1)[1])
            msg = email.message_from_bytes(raw_email)

            # Decode email subject
            subject, encoding = decode_header(msg['Subject'])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or 'utf-8')

            # Get email sender
            sender = msg.get('From')

            # Extract email body (text/plain content)
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == 'text/plain':
                        content = part.get_payload(decode=True).decode('utf-8')
                        save_email_to_db(subject, sender, content)
            else:
                content = msg.get_payload(decode=True).decode('utf-8')
                logging.info(f"Email from: {msg.get('From')}, Subject: {subject[:50]}..., Content: {content[:100]}...")
                save_email_to_db(subject, sender, content)

        pop_conn.quit()
    except Exception as e:
        logging.error(f"Error fetching emails via POP3: {e}")

# Main function to poll emails based on the protocol
def poll_emails():
    try:
        protocol = mail_config['protocol'].lower()
        if protocol == 'imap':
            logging.info("Using IMAP to fetch emails")
            fetch_emails_imap()
        elif protocol == 'pop3':
            logging.info("Using POP3 to fetch emails")
            fetch_emails_pop3()
        else:
            logging.info(f"Invalid protocol specified: {protocol}")
    except Exception as e:
        logging.error(f"Error polling emails: {e}")

# Run the script every 5 minutes
if __name__ == "__main__":
    while True:
        logging.info("Starting...")
        poll_emails()
        logging.info("Poll finished, waiting 5 minutes...")
        # Sleep for 5 minutes
        time.sleep(300)
