import pandas as pd
from PyPDF2 import PdfReader
import io

def parse_file(uploaded_file):
    """Converts various file types into a string summary for the AI."""
    file_type = uploaded_file.name.split('.')[-1].lower()
    
    if file_type == 'csv':
        df = pd.read_csv(uploaded_file)
        return df.to_csv(index=False), df
    
    elif file_type in ['xlsx', 'xls']:
        df = pd.read_excel(uploaded_file)
        return df.to_csv(index=False), df
    
    elif file_type == 'pdf':
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        # For PDF, we return text and a None for the DataFrame (or try to extract tables)
        return text, None
    
    return "Unsupported file type", None