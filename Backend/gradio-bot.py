import gradio as gr
import time
import base64
import PyPDF2
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
import autogen

# Initialisierung des LLM
llm = Ollama(model="gemma:2b")

pdf_path = "Backend/static/files/LLM.pdf"


def load_pdf_to_base64(pdf_path):
    """Lädt ein PDF und konvertiert es in einen base64-String zur Einbettung in HTML."""
    with open(pdf_path, "rb") as pdf_file:
        pdf_base64 = base64.b64encode(pdf_file.read()).decode('utf-8')
    return f"data:application/pdf;base64,{pdf_base64}"

def extract_text_from_pdf(path_file: str):
    with open(path_file, 'rb') as pdf:
        reader = PyPDF2.PdfReader(pdf, strict=False)
        pdf_text = []
        
        for page in reader.pages:
            content = page.extract_text()
            pdf_text.append(content)
        
        return "".join(pdf_text)

def respond(message, chat_history):
    pdf_text = extract_text_from_pdf(pdf_path)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"You are an expert about the topic from this extracted text from a PDF file: >>>{pdf_text}<<<"),
        ("user", "{input}")
    ])

    chain = prompt | llm 
    
    bot_message = chain.invoke({"input": message})
    
    # Chat-Historie aktualisieren
    chat_history.append((message, bot_message))
    
    return "", chat_history

theme = gr.themes.Monochrome(text_size="sm" ,primary_hue=gr.themes.colors.red, secondary_hue=gr.themes.colors.indigo, font=[gr.themes.GoogleFont("Inconsolata"), "Arial", "sans-serif"])

css = """
    .gradio-container {
        background-color: #3c3c3c;
    }
"""

with gr.Blocks(theme=theme, css=css) as demo:    
    with gr.Row():
        with gr.Column():
            
            
            pdf_base64 = load_pdf_to_base64(pdf_path)
            pdf_html = f'<iframe src="{pdf_base64}" width="100%" height="853px" style="border:none;"></iframe>'
            extracted_text = extract_text_from_pdf(path_file=pdf_path)
            gr.HTML(value=pdf_html)
            
            gr.Button(link="/", value="Back to PDF collection")
            
        with gr.Column():

            dropdown = gr.Dropdown(
                ["gemma:2b", "GPT4.0"], label="LLM", show_label=True, value="gemma:2b"
            )
            llm = Ollama(model=dropdown.value)
            chatbot = gr.Chatbot(height=600)
            msg = gr.Textbox()
            
            with gr.Row():
                download_json = gr.DownloadButton("Download JSON", visible=True)  # noch keine Funktionen
                clear = gr.ClearButton([msg, chatbot])
    
    msg.submit(respond, [msg, chatbot], [msg, chatbot])

demo.launch()