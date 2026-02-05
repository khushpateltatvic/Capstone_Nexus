import mailbox
import os
import sys
import requests
import re
from email.header import decode_header
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

# --- Configuration ---
API_URL = "http://localhost:8000/api/v1"
AUTH_USER = {"email": "ravi@tatvic.com", "password": "Admin@123"}
CHUNK_SIZE = 50  # Safe batch size for full-length emails

# --- Helper Functions ---

def clean_text(text):
    """
    Aggressively removes CSS, Scripts, HTML tags, and extra whitespace,
    BUT keeps all the actual content text.
    """
    if not text:
        return ""
    
    # 1. Remove CSS and Script blocks (content inside <style>...</style>)
    # re.DOTALL makes . match newlines too, stripping the whole block
    text = re.sub(r'<style.*?>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # 2. Remove Image tags (we don't need the image URLs for text embedding)
    text = re.sub(r'<img.*?>', '', text, flags=re.IGNORECASE)
    
    # 3. Remove remaining HTML tags (leaving just the text inside them)
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # 4. Collapse multiple spaces/newlines into clean lines
    # This turns "Word      \n     Word" into "Word Word"
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def decode_header_safe(header_val):
    """Safely decodes email headers."""
    if not header_val:
        return ""
    try:
        decoded = decode_header(header_val)
        parts = []
        for content, encoding in decoded:
            if isinstance(content, bytes):
                parts.append(content.decode(encoding or 'utf-8', errors='replace'))
            else:
                parts.append(str(content))
        return "".join(parts)
    except Exception:
        return str(header_val)

def get_body(message):
    """
    Extracts text. Prioritizes text/plain. 
    If only HTML exists, it strips tags/CSS but KEEPS all text content.
    """
    body = ""
    html_body = None
    
    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            # Skip attachments (files), but keep text parts
            if "attachment" in content_disposition:
                continue

            try:
                payload = part.get_payload(decode=True)
                if not payload: 
                    continue
                
                decoded_text = payload.decode('utf-8', errors='replace')
                
                if content_type == "text/plain":
                    body += decoded_text
                elif content_type == "text/html":
                    # Save HTML just in case there is no plain text
                    html_body = decoded_text
            except Exception:
                continue
    else:
        # Non-multipart
        try:
            payload = message.get_payload(decode=True)
            if payload:
                text = payload.decode('utf-8', errors='replace')
                if message.get_content_type() == "text/html":
                    html_body = text
                else:
                    body = text
        except Exception:
            pass

    # Logic: If we found plain text, use it. If not, use the HTML body.
    final_text = body if body.strip() else (html_body or "")
    
    # Clean it (Remove CSS/JS/Tags) but DO NOT LIMIT LENGTH
    return clean_text(final_text)

def get_auth_token():
    """Logs in and retrieves the JWT token."""
    try:
        resp = requests.post(
            f"{API_URL}/auth/login/access-token",
            data={"username": AUTH_USER["email"], "password": AUTH_USER["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
        else:
            print(f"❌ Auth Failed: {resp.status_code}")
            return None
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return None

def format_email_text(email_data):
    """Formats email data into a single text block."""
    return (
        f"Subject: {email_data['subject']}\n"
        f"From: {email_data['from']}\n"
        f"To: {email_data['to']}\n"
        f"Date: {email_data['date']}\n\n"
        f"{email_data['body']}\n"
        + "="*50 + "\n"
    )

def filter_emails(filepath):
    """Generator: filters emails by date (Oct-Dec 2025) and yields valid ones."""
    mbox = mailbox.mbox(filepath)
    
    for message in mbox:
        try:
            date_str = message.get('date')
            if not date_str:
                continue
                
            email_date = parsedate_to_datetime(date_str)
            if email_date.tzinfo is None:
                email_date = email_date.replace(tzinfo=timezone.utc)
            
            # --- NO FILTER: Yield all valid emails ---
            yield {
                "subject": decode_header_safe(message.get('subject', 'No Subject')),
                "from": decode_header_safe(message.get('from', 'Unknown')),
                "to": decode_header_safe(message.get('to', '')),
                "date": date_str,
                "body": get_body(message)
            }
        except Exception:
            continue

# --- Main Execution ---

def main():
    if len(sys.argv) > 1:
        mbox_path = sys.argv[1]
    else:
        # Check multiple common locations for reliability
        script_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths = [
            os.path.join(script_dir, "..", "app", "data", "icicilombard@tatvic.com--icicilombard@tatvic.com_0.mbox"),
            os.path.join(script_dir, "..", "..", "data", "icicilombard@tatvic.com--icicilombard@tatvic.com_0.mbox"),
            os.path.join(script_dir, "..", "data", "icicilombard@tatvic.com--icicilombard@tatvic.com_0.mbox"),
            os.path.join(script_dir, "..", "app", "data", "emaildata.mbox"),
            os.path.join(script_dir, "..", "..", "data", "emaildata.mbox"),
            os.path.join(script_dir, "..", "data", "emaildata.mbox"),
        ]
        
        mbox_path = None
        for p in possible_paths:
            # Must exist AND have content
            if os.path.exists(p) and os.path.getsize(p) > 0:
                mbox_path = p
                break
        
        if not mbox_path:
             # Default to the first one for error message if none exist
             mbox_path = possible_paths[0]

    if not os.path.exists(mbox_path):
        print(f"File not found: {mbox_path}")
        return

    token = get_auth_token()
    if not token:
        return
    
    headers = {
        "Authorization": f"Bearer {token}", 
        "Content-Type": "application/json"
    }

    print(f"Processing MBOX: {mbox_path}")
    print("Processing All Timeframes (Full Content, No CSS)...")

    batch = []
    chunk_counter = 1

    for email in filter_emails(mbox_path):
        batch.append(email)

        # Send batch when full
        if len(batch) >= CHUNK_SIZE:
            print(f"Chunk {chunk_counter} sending ({len(batch)} emails)...", end=" ", flush=True)
            
            # Create a list of documents, one per email
            documents = []
            for i, e in enumerate(batch):
                documents.append({
                    "text": format_email_text(e),
                    "metadata": {
                        "filename": f"mbox_email_{chunk_counter}_{i}.txt",
                        "subject": e['subject'],
                        "from": e['from'],
                        "date": e['date'],
                        "source": "mbox_import"
                    }
                })
            
            payload = {
                "documents": documents,
                "client_id": "email_archive",
                "project_id": "mbox_import"
            }
            
            try:
                resp = requests.post(f"{API_URL}/automation/ingest-batch", json=payload, headers=headers)
                if resp.status_code == 200:
                    print(f"Completed.")
                else:
                    print(f"Failed ({resp.status_code}).")
            except Exception as e:
                print(f"Error: {e}")

            batch = []
            chunk_counter += 1

    # Send leftovers
    if batch:
        print(f"Chunk {chunk_counter} (Final) sending...", end=" ", flush=True)
        
        documents = []
        for i, e in enumerate(batch):
            documents.append({
                "text": format_email_text(e),
                "metadata": {
                    "filename": f"mbox_email_final_{i}.txt",
                    "subject": e['subject'],
                    "from": e['from'],
                    "date": e['date'],
                    "source": "mbox_import"
                }
            })
            
        payload = {
            "documents": documents,
            "client_id": "email_archive",
            "project_id": "mbox_import"
        }
        try:
            requests.post(f"{API_URL}/automation/ingest-batch", json=payload, headers=headers)
            print(f"Completed.")
        except Exception as e:
            print(f"Error: {e}")

    print("\nAll done.")

if __name__ == "__main__":
    main()