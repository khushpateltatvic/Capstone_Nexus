from bs4 import BeautifulSoup
import logging
import email
from email.policy import default

class EmailParser:
    def parse(self, content: bytes) -> str:
        """
        Parses raw email bytes (.eml) or HTML content.
        """
        try:
            # Try parsing as EML first
            msg = email.message_from_bytes(content, policy=default)
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                         body += part.get_content()
                    elif part.get_content_type() == "text/html":
                         soup = BeautifulSoup(part.get_content(), "html.parser")
                         body += soup.get_text(separator="\n")
            else:
                # Single part
                payload = msg.get_content()
                if msg.get_content_type() == "text/html":
                     soup = BeautifulSoup(payload, "html.parser")
                     body = soup.get_text(separator="\n")
                else:
                     body = payload
            
            # Metadata injection (could be separated)
            subject = msg.get("subject", "")
            sender = msg.get("from", "")
            
            return f"Subject: {subject}\nFrom: {sender}\n\n{body}"
            
        except Exception as e:
            logging.warning(f"Email parse failed as EML, trying raw HTML: {e}")
            try:
                soup = BeautifulSoup(content, "html.parser")
                return soup.get_text(separator="\n")
            except Exception as e2:
                logging.error(f"Email/HTML parse fatal error: {e2}")
                return ""
