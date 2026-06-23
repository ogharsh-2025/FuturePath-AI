import re
import io
from pypdf import PdfReader
from docx import Document

class ResumeParser:
    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        """
        Extracts raw text from a PDF file.
        """
        try:
            pdf = PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
        except Exception as e:
            raise ValueError(f"Error parsing PDF: {str(e)}")

    @staticmethod
    def extract_text_from_docx(file_bytes: bytes) -> str:
        """
        Extracts raw text from a DOCX file.
        """
        try:
            doc = Document(io.BytesIO(file_bytes))
            text = []
            for paragraph in doc.paragraphs:
                text.append(paragraph.text)
            return "\n".join(text)
        except Exception as e:
            raise ValueError(f"Error parsing DOCX: {str(e)}")

    @classmethod
    def parse_resume(cls, file_bytes: bytes, filename: str) -> dict:
        """
        Determines file type, extracts text, and parses fields (name, email, phone, education, experience).
        """
        filename_lower = filename.lower()
        if filename_lower.endswith(".pdf"):
            text = cls.extract_text_from_pdf(file_bytes)
        elif filename_lower.endswith(".docx") or filename_lower.endswith(".doc"):
            text = cls.extract_text_from_docx(file_bytes)
        else:
            raise ValueError("Unsupported file format. Please upload a PDF or DOCX file.")

        return {
            "text": text,
            "name": cls.extract_name(text),
            "email": cls.extract_email(text),
            "phone": cls.extract_phone(text),
            "education": cls.extract_section(text, ["education", "academic", "studies", "degree", "university", "college"]),
            "experience": cls.extract_section(text, ["experience", "work history", "employment", "professional experience", "work experience", "career history"])
        }

    @staticmethod
    def extract_email(text: str) -> str | None:
        email_regex = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        match = re.search(email_regex, text)
        return match.group(0) if match else None

    @staticmethod
    def extract_phone(text: str) -> str | None:
        # Matches common patterns like +1-234-567-8901, (123) 456-7890, 1234567890, etc.
        phone_regex = r'(?:(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b\d{10}\b)'
        match = re.search(phone_regex, text)
        return match.group(0) if match else None

    @staticmethod
    def extract_name(text: str) -> str | None:
        """
        Extracts name from the first non-empty line of the resume.
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if not lines:
            return None
        # Often the name is at the top of the resume. Check the first line.
        first_line = lines[0]
        # Clean non-alphabetical characters except spaces
        clean_name = re.sub(r'[^a-zA-Z\s]', '', first_line).strip()
        words = clean_name.split()
        if 1 <= len(words) <= 4:
            return " ".join(words)
        return "Resume Profile"

    @staticmethod
    def extract_section(text: str, keywords: list[str]) -> str:
        """
        Extracts text belonging to sections matching the specified keywords.
        Runs a stateful parser through the lines.
        """
        lines = text.split('\n')
        section_content = []
        in_section = False
        
        # Stop indicators representing headers of other sections
        stop_keywords = [
            "education", "experience", "work history", "employment", 
            "skills", "projects", "certifications", "languages", 
            "summary", "objective", "contact", "about me", "references", "skills & tools"
        ]
        
        for line in lines:
            line_clean = line.strip().lower()
            if not line_clean:
                continue
            
            # Detect section start
            # Check if line contains one of the keywords and is relatively short (typical header)
            if len(line.strip()) < 40 and any(re.search(rf'\b{kw}\b', line_clean) for kw in keywords):
                in_section = True
                continue
                
            # If in section, check if we hit another section header to stop
            if in_section:
                # If the line looks like a header of a different section, stop parsing
                if len(line.strip()) < 40 and any(re.search(rf'\b{kw}\b', line_clean) for kw in stop_keywords if kw not in keywords):
                    in_section = False
                    break
                section_content.append(line.strip())
                
        return "\n".join(section_content) if section_content else "Not specified"
