
import logging

class TextParser:
    """Simple parser for plain text files."""
    def parse(self, content: bytes) -> str:
        """
        Parses raw bytes from a text file into a string.
        """
        try:
            if isinstance(content, str):
                return content
            return content.decode("utf-8", errors="ignore")
        except Exception as e:
            logging.error(f"Text parse failed: {e}")
            return ""
