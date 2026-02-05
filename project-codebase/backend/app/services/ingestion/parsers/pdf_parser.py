import io
import logging
from pypdf import PdfReader

class PDFParser:
    def parse(self, content: bytes) -> str:
        """
        Extracts text from PDF content using pypdf.
        """
        try:
            reader = PdfReader(io.BytesIO(content))
            text_content = []
            for page in reader.pages:
                text_content.append(page.extract_text())
            return "\n".join(text_content)
        except Exception as e:
            logging.error(f"PDF Parse error: {e}")
            return ""
