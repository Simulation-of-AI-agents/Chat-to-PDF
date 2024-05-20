import gradio as gr
import PyPDF2
from openai import OpenAI
import configparser
from gradio_pdf import PDF
import base64


# Laden des API-Schlüssels aus der Konfigurationsdatei
config = configparser.ConfigParser()
config_file_path = 'Backend/key.secret'
config.read(config_file_path)
api_key = config['GWDG']['API_KEY']

# Basis-URL für die API
base_url = "https://chat-ai.academiccloud.de/v1"

# Verfügbare Modelle
models = ["intel-neural-chat-7b", "mixtral-8x7b-instruct", "qwen1.5-72b-chat", "meta-llama-3-70b-instruct"]

# OpenAI-Client erstellen
client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

# CSS für das Design
css = """
    .gradio-container {
        background-color: grey;
    }
"""

pdf_name = "No PDF file uploaded"

theme = gr.themes.Monochrome(text_size="sm" ,primary_hue=gr.themes.colors.red, secondary_hue=gr.themes.colors.indigo, font=[gr.themes.GoogleFont("Inconsolata"), "Arial", "sans-serif"])

pdf_collection = []

def load_pdf_to_base64(pdf_path):

    with open(pdf_path, "rb") as pdf_file:
        pdf_base64 = base64.b64encode(pdf_file.read()).decode('utf-8')
    return f"data:application/pdf;base64,{pdf_base64}"


# Funktion zum Extrahieren von Text aus einem PDF
def extract_text_from_pdf(path_file: str):
    with open(path_file, 'rb') as pdf:
        reader = PyPDF2.PdfReader(pdf, strict=False)
        pdf_text = []
        
        for page in reader.pages:
            content = page.extract_text()
            pdf_text.append(content)
        
        return "".join(pdf_text)

# Funktion zum Verarbeiten der Nachricht und Abrufen der Antwort vom Modell
def respond(message, chat_history, model):
    chat_completion = client.chat.completions.create(
        messages=[{"role": "system", "content": "You are a helpful assistant"}, {"role": "user", "content": message}],
        model=model,
    )

    chat_history.append((message, chat_completion.choices[0].message.content))
    
    return "", chat_history


def enable_textbox(pdf_file):
    if pdf_file:
        pdf_collection = list(pdf.temp_files)
        return gr.update(interactive=True), f"PDF File Path: {pdf_file}", gr.Dropdown(choices=pdf_collection, value=pdf_collection[0])
    return gr.update(interactive=False), "No PDF file uploaded", gr.Dropdown(choices=pdf_collection, value=pdf_collection[0])

# Gradio-Interface erstellen
with gr.Blocks(theme=theme, css=css) as demo:
    #TODO:Bisher kann man in der DropDown noch keine PDF auswählen und sie wird angezeigt 
    pdf_collection_dropdown = gr.Dropdown( 
                choices=pdf_collection, label="PDF Collection", show_label=True, interactive=True
            )
    
    with gr.Row():
        with gr.Column():

            pdf = PDF(label="Upload a PDF", interactive=True, height=750)
            
            # pdf_base64 = load_pdf_to_base64(pdf_collection_dropdown.value)
            # pdf_html = f'<iframe src="{pdf_base64}" width="100%" height="853px" style="border:none;"></iframe>'
            name = gr.Markdown(value=pdf_name, render=True, visible=False)

        with gr.Column():
            dropdown = gr.Dropdown(
                models, label="LLM", show_label=True, value=models[0]
            )
            with gr.Group():
                with gr.Row():
                    download_json = gr.Button("Download JSON", visible=True)  # noch keine Funktionen
                    clear = gr.Button("Clear")
                chatbot = gr.Chatbot(height=580)
            
                msg = gr.Textbox(label="Enter your message", interactive=False)  # initially disabled

    # Datei hochladen und Textbox aktivieren
    pdf.upload(lambda x: enable_textbox(x), pdf, [msg, name, pdf_collection_dropdown])

    # Ereignis, wenn eine Nachricht gesendet wird
    msg.submit(respond, [msg, chatbot, dropdown], [msg, chatbot])
    
    # Ereignis für die Clear-Taste
    clear.click(lambda: None, None, chatbot, queue=False)
    
# Starten der Gradio-App
demo.launch(share=False)