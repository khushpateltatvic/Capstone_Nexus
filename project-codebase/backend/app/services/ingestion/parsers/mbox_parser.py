"""
MBOX Email Parser - Enhanced Version

Parses .mbox files with FULL content extraction for large email archives.
- Extracts complete email bodies (no truncation)
- Sorts by date (most recent first)
- Handles multiple encodings
- Preserves threading information
"""

import mailbox
import logging
from typing import List, Dict, Any, Optional
from email.utils import parsedate_to_datetime
from email.header import decode_header, make_header
from html import unescape
from datetime import datetime
import re


class MboxParser:
    """Enhanced parser for MBOX email archive files."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        
    def _decode_header(self, header_value: str) -> str:
        """Decode email header with proper encoding handling."""
        if not header_value:
            return ""
        try:
            decoded = make_header(decode_header(header_value))
            return str(decoded)
        except:
            return str(header_value)
        
    def _clean_html(self, html_content: str) -> str:
        """Strip HTML tags and decode entities, preserving structure."""
        # Remove script and style elements
        clean = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        # Convert br/p tags to newlines
        clean = re.sub(r'<br\s*/?>', '\n', clean, flags=re.IGNORECASE)
        clean = re.sub(r'</p>', '\n\n', clean, flags=re.IGNORECASE)
        clean = re.sub(r'</div>', '\n', clean, flags=re.IGNORECASE)
        clean = re.sub(r'</li>', '\n', clean, flags=re.IGNORECASE)
        # Remove remaining HTML tags
        clean = re.sub(r'<[^>]+>', '', clean)
        # Decode HTML entities
        clean = unescape(clean)
        # Normalize whitespace (but preserve newlines)
        clean = re.sub(r'[ \t]+', ' ', clean)
        clean = re.sub(r'\n\s*\n\s*\n', '\n\n', clean)
        return clean.strip()
    
    def _get_body(self, message) -> str:
        """Extract FULL plain text body from email message."""
        body = ""
        html_body = ""
        
        if message.is_multipart():
            for part in message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                    
                if content_type == "text/plain":
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode(charset, errors='ignore')
                    except:
                        pass
                elif content_type == "text/html" and not body:
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        payload = part.get_payload(decode=True)
                        if payload:
                            html_body = payload.decode(charset, errors='ignore')
                    except:
                        pass
        else:
            try:
                charset = message.get_content_charset() or 'utf-8'
                payload = message.get_payload(decode=True)
                if payload:
                    body = payload.decode(charset, errors='ignore')
                    if message.get_content_type() == "text/html":
                        body = self._clean_html(body)
            except:
                body = str(message.get_payload())
        
        # If no plain text, use cleaned HTML
        if not body and html_body:
            body = self._clean_html(html_body)
        
        return body.strip()
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse email date with fallback."""
        if not date_str:
            return None
        try:
            return parsedate_to_datetime(date_str)
        except:
            return None
    
    def parse(self) -> List[Dict[str, Any]]:
        """Parse MBOX file and return list of ALL email documents."""
        emails = []
        
        try:
            mbox = mailbox.mbox(self.filepath)
            total = len(mbox)
            logging.info(f"Parsing {total} emails from {self.filepath}...")
            
            for i, message in enumerate(mbox):
                if i % 100 == 0:
                    logging.info(f"  Processed {i}/{total} emails...")
                    
                try:
                    # Extract and decode metadata
                    subject = self._decode_header(message.get('subject', 'No Subject'))
                    from_addr = self._decode_header(message.get('from', 'Unknown'))
                    to_addr = self._decode_header(message.get('to', ''))
                    cc_addr = self._decode_header(message.get('cc', ''))
                    date_str = message.get('date', '')
                    message_id = message.get('message-id', f'msg_{i}')
                    in_reply_to = message.get('in-reply-to', '')
                    thread_id = message.get('references', '').split()[0] if message.get('references') else ''
                    
                    # Parse date
                    date_obj = self._parse_date(date_str)
                    date_iso = date_obj.isoformat() if date_obj else None
                    
                    # Get FULL body (no truncation)
                    body = self._get_body(message)
                    
                    # Get attachment names (but not content)
                    attachments = []
                    if message.is_multipart():
                        for part in message.walk():
                            filename = part.get_filename()
                            if filename:
                                attachments.append(self._decode_header(filename))
                    
                    if body or subject != 'No Subject':  # Include emails with content or subject
                        emails.append({
                            "message_id": message_id,
                            "subject": subject,
                            "from": from_addr,
                            "to": to_addr,
                            "cc": cc_addr,
                            "date": date_iso,
                            "date_obj": date_obj,
                            "body": body,  # FULL body, no truncation
                            "in_reply_to": in_reply_to,
                            "thread_id": thread_id,
                            "attachments": attachments,
                            "index": i
                        })
                        
                except Exception as e:
                    logging.warning(f"Error parsing email {i}: {e}")
                    continue
            
            mbox.close()
            logging.info(f"Successfully parsed {len(emails)} emails from {self.filepath}")
            
        except Exception as e:
            logging.error(f"Error opening MBOX file {self.filepath}: {e}")
        
        # Sort by date (newest first)
        emails.sort(key=lambda e: e.get("date_obj") or datetime.min, reverse=True)
        
        return emails
    
    def to_text(self, emails: List[Dict] = None) -> str:
        """Convert parsed emails to comprehensive text for embedding."""
        if emails is None:
            emails = self.parse()
        
        lines = [
            "# EMAIL ARCHIVE",
            f"Total emails: {len(emails)}",
            f"Date range: {emails[-1].get('date', 'Unknown') if emails else 'N/A'} to {emails[0].get('date', 'Unknown') if emails else 'N/A'}",
            "",
            "---",
            ""
        ]
        
        for email in emails:
            subject = email.get('subject', 'No Subject')
            from_addr = email.get('from', 'Unknown')
            to_addr = email.get('to', '')
            cc = email.get('cc', '')
            date = email.get('date', 'Unknown')
            body = email.get('body', '')
            attachments = email.get('attachments', [])
            
            lines.append(f"## {subject}")
            lines.append(f"From: {from_addr}")
            lines.append(f"To: {to_addr}")
            if cc:
                lines.append(f"CC: {cc}")
            lines.append(f"Date: {date}")
            if attachments:
                lines.append(f"Attachments: {', '.join(attachments)}")
            lines.append("")
            
            # FULL body content
            if body:
                lines.append(body)
            
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
    
    def to_chunks(self, emails: List[Dict] = None, chunk_size: int = 10) -> List[str]:
        """Split emails into chunks for better embedding performance."""
        if emails is None:
            emails = self.parse()
        
        chunks = []
        for i in range(0, len(emails), chunk_size):
            batch = emails[i:i + chunk_size]
            chunk_text = self.to_text(batch)
            chunks.append(chunk_text)
        
        return chunks
