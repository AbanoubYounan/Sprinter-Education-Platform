import PyPDF2 
import logging
import os

logger = logging.getLogger(__name__)

class PDFSearchTool:
    def __init__(self, config: dict):
        self.config = config

    def extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extracts text content from a PDF using PyPDF2.
        """
        extracted_text = ""
        try:
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text + "\n"
        except Exception as e:
            logger.error("Error extracting text from PDF: %s", e)
        return extracted_text

    def process(self, file_path: str) -> str:
        """
        Extracts the text content from the PDF. If extraction fails,
        returns a fallback message.
        """
        extracted_content = self.extract_text_from_pdf(file_path)
        if extracted_content:
            return extracted_content
        else:
            return f"Could not extract text from {os.path.basename(file_path)}. It might be an image-based PDF."