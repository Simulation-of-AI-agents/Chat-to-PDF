import gradio as gr
from autogen import AssistantAgent, UserProxyAgent
import time
import base64
import PyPDF2


config_list = [
  {
    "model": "codellama",
    "base_url": "http://localhost:11434/v1",
    "api_key": "ollama",
  }
]

assistant = AssistantAgent("assistant", llm_config={"config_list": config_list})

user_proxy = UserProxyAgent("user_proxy", code_execution_config={"work_dir": "coding", "use_docker": False})
user_proxy.initiate_chat(assistant, message="What is the best series of all time?")


pdf_path = "Backend/static/files/Hello_World.pdf"
    
def load_pdf_to_base64(pdf_path):
    """Lädt ein PDF und konvertiert es in einen base64-String zur Einbettung in HTML."""
    with open(pdf_path, "rb") as pdf_file:
        pdf_base64 = base64.b64encode(pdf_file.read()).decode('utf-8')
    return f"data:application/pdf;base64,{pdf_base64}"

def respond(message, chat_history):
    pdf_text = extract_text_from_pdf(path_file=pdf_path)
    bot_message = pdf_text
    chat_history.append((message, bot_message))
    time.sleep(2)
    return "", chat_history

def extract_text_from_pdf(path_file: str):
    with open(path_file, 'rb') as pdf:
        reader = PyPDF2.PdfReader(pdf, strict=False)
        pdf_text = []
        
        for page in reader.pages:
            content = page.extract_text()
            pdf_text.append(content)
        
        return "".join(pdf_text)

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
            pdf_html = f'<iframe src="{pdf_base64}" width="100%" height="1000px" style="border:none;"></iframe>'
            extrated_text_list = extract_text_from_pdf(path_file=pdf_path)
            extracted_text = "".join(extrated_text_list)
            gr.HTML(value=pdf_html)

        with gr.Column():
            dropdown = gr.Dropdown(
                ["GPT-4.0", "Mistral"], label="LLM"
            )
            chatbot = gr.Chatbot(height=635)
            msg = gr.Textbox()
            
            with gr.Row():
                download_json = gr.DownloadButton("Download JSON", visible=True)  # noch keine Funktionen
                clear = gr.ClearButton([msg, chatbot])
    
    msg.submit(respond, [msg, chatbot], [msg, chatbot])

demo.launch()
