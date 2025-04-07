from langchain_community.tools import WikipediaQueryRun, DuckDuckGoSearchRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.tools import Tool
from datetime import datetime
from fpdf import FPDF
import os

def txt_to_pdf(txt_filename, pdf_filename):
    """Convert a text file to PDF"""
    try:
        if not os.path.exists(txt_filename):
            raise FileNotFoundError(f"The file {txt_filename} does not exist.")
        
        # Here's a simple implementation using reportlab (you might have a different implementation)
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        from reportlab.lib.units import inch
        
        doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        with open(txt_filename, 'r') as f:
            content = f.read()
            
        # Split content into paragraphs
        paragraphs = content.split('\n\n')
        for text in paragraphs:
            if text.strip():
                p = Paragraph(text.replace('\n', '<br/>'), styles['Normal'])
                story.append(p)
        
        doc.build(story)
        
        if not os.path.exists(pdf_filename):
            raise FileNotFoundError(f"Failed to create PDF file at {pdf_filename}")
            
        return True
        
    except Exception as e:
        print(f"Error in txt_to_pdf: {e}")
        raise

def save_to_file(data: str, filename: str="research_output.txt"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_text = f"--- Query Output ---\nTimestamp: {timestamp}\n\n{data}\n\n"

    folder_path = "static/downloads"

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    file_path = os.path.join(folder_path, filename)

    with open(file_path, "a", encoding="utf-8") as f:
        f.write(formatted_text)

    return f"Data successfully saved to {file_path}/{filename}."

save_tool = Tool(
    name="save_text_to_file",
    func=save_to_file,
    description="Saves structured web search data to a text file."
)

search = DuckDuckGoSearchRun()
duck_tool = Tool(
    name="search",
    func=search.run,
    description="Search the web for information"
)

# free 3rd party tools
api_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=100, lang="en")
wiki_tool = WikipediaQueryRun(api_wrapper=api_wrapper)