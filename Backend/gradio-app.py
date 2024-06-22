import os
import socket
import subprocess
import sys
import gradio as gr
import PyPDF2
import configparser
import base64
import warnings
import json

from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA

warnings.filterwarnings("ignore", category=FutureWarning)
os.environ["TOKENIZERS_PARALLELISM"] = "false"

PORT = 7860

# Function to check if port is in use
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# Function to free the port if it's in use
def free_port(port):
    if is_port_in_use(port):
        print(f"Port {port} is in use, attempting to free it.")
        if sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
            # Unix-based systems
            result = subprocess.run(['lsof', '-t', f'-i:{port}'], capture_output=True, text=True)
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    subprocess.run(['kill', '-9', pid])
        elif sys.platform.startswith("win"):
            # Windows systems
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
            lines = result.stdout.splitlines()
            for line in lines:
                if f"0.0.0.0:{port}" in line or f"127.0.0.1:{port}" in line:
                    pid = line.strip().split()[-1]
                    subprocess.run(['taskkill', '/PID', pid, '/F'])
        else:
            raise OSError("Unsupported operating system")

        print(f"Port {port} has been freed.")

# Ensure the port is available
free_port(PORT)

# Set the port environment variable
os.environ["GRADIO_SERVER_PORT"] = str(PORT)

# Read the API key from config file
config = configparser.ConfigParser()
config_file_path = 'Backend/key.secret'
config.read(config_file_path)
api_key = config['GWDG']['API_KEY']

# Define the base URL for the API
base_url = "https://chat-ai.academiccloud.de/v1"

# List of available models
models = ["mixtral-8x7b-instruct", "meta-llama-3-70b-instruct", "intel-neural-chat-7b", "qwen1.5-72b-chat"]

# Initialize variables
uploaded_files = []
vector_store_cache = {}  # Cache for storing vector stores
selected_model = models[0]  # Default model
model = ChatOpenAI(model_name=selected_model, openai_api_key=api_key, openai_api_base=base_url, temperature=0)  # Use the selected model

def get_file_name(file_path):
    return os.path.basename(file_path)

def sync_dropdown(selected_file_name, all_files):
    for file in all_files:
        if get_file_name(file) == selected_file_name:
            return file
    return ""

def change_pdf(value):
    pdf_base64 = load_pdf_to_base64(value)
    pdf_html = f'<iframe src="{pdf_base64}" width="100%" height="763px"></iframe>'
    chat_history = load_chat_history(value)  # Load history
    return pdf_html, chat_history

def chunk_processing(pdf):
    pdf_reader = PyPDF2.PdfReader(pdf)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text=text)
    return chunks

def download_json_action(pdf_file):
    # Ensure vector store is available
    if pdf_file not in vector_store_cache:
        chunks = chunk_processing(pdf_file)
        vector_store_cache[pdf_file] = embeddings(chunks)

    vector_store = vector_store_cache[pdf_file]

    # Questions related to the fields in the SustainabilityReport
    questions = {
        "CO2": "Answer this question with just a single float value, Make sure that you have recalculated the value correctly if necessary!, NO WORDS OR DIGITS: What is the latest CO2 emissions in tons/annum?",
        "NOX": "Answer this question with just a single float value, Make sure that you have recalculated the value correctly if necessary!, NO WORDS OR DIGITS: What is the latest NOX emissions in tons/annum?",
        "Number_of_Electric_Vehicles": "Answer this question with just a single float value, NO WORDS OR DIGITS: How many electric vehicles are mentioned?",
        "Impact": "Summarize the negative impact on climate change addressed in the report. IMPORTANT: Answer in min 20 and max 50 Words",
        "Risks": "What are the material risks related to climate change? IMPORTANT: Answer in min 20 and max 50 Words",
        "Opportunities": "Summarize the financial materiality related to climate change. IMPORTANT: Answer in min 20 and max 50 Words",
        "Strategy": "Describe the company's strategy and business model for a sustainable economy. IMPORTANT: Answer in min 20 and max 50 Words",
        "Actions": "What actions and resources are mentioned in relation to sustainability? IMPORTANT: Answer in min 20 and max 50 Words",
        "Adopted_policies": "What policies has the company adopted for sustainability? IMPORTANT: Answer in min 20 and max 50 Words",
        "Targets": "What are the company's goals for a sustainable economy? IMPORTANT: Answer in min 20 and max 50 Words"
    }

    results = {}
    
    for key, question in questions.items():
        results[key] = extract_information(vector_store, question)
    
    # Add the PDF file name to the results
    results["name"] = os.path.basename(pdf_file)

    # Directory to store JSON files
    output_dir = os.path.join(os.path.dirname(__file__), 'json_reports')
    os.makedirs(output_dir, exist_ok=True)  # Create directory if it does not exist

    # Create the JSON filename
    json_file_name = os.path.splitext(os.path.basename(pdf_file))[0] + ".json"
    json_file_path = os.path.join(output_dir, json_file_name)

    # Save results to JSON file with formatted output
    with open(json_file_path, 'w') as f:
        json.dump(results, f, indent=4, sort_keys=False)
    
    return json_file_path

def extract_information(vector_store, question):
    retriever = vector_store.as_retriever()
    model = ChatOpenAI(model_name=selected_model, openai_api_key=api_key, openai_api_base=base_url, temperature=0)  # Use the selected model
    qa = RetrievalQA.from_chain_type(llm=model, chain_type="stuff", retriever=retriever, return_source_documents=False)
    result = qa.invoke(f"Extract information: {question}")
    return result["result"] if result else "Value not found"

def embeddings(chunks):
    embeddings_model_name = "sentence-transformers/all-MiniLM-L6-v2"
    embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)
    vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    return vector_store

def extract_text_from_pdf(path_file: str):
    with open(path_file, 'rb') as pdf:
        reader = PyPDF2.PdfReader(pdf, strict=False)
        pdf_text = []
        
        for page in reader.pages:
            content = page.extract_text()
            pdf_text.append(content)
        
        return "".join(pdf_text)

def generation_with_history(VectorStore, prompt_text):
    retriever = VectorStore.as_retriever()
    model = ChatOpenAI(model_name=selected_model, openai_api_key=api_key, openai_api_base=base_url, temperature=0)  # Use the selected model
    qa = RetrievalQA.from_chain_type(llm=model, chain_type="refine", retriever=retriever, return_source_documents=False)
    result = qa.invoke(f"Answer with maximum 1000 characters:{prompt_text}")
    return result

def load_chat_history(pdf_file):
    history_file = pdf_file + '.json'
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            return json.load(f)
    return []

def load_pdf_to_base64(pdf_path):
    with open(pdf_path, "rb") as pdf_file:
        pdf_base64 = base64.b64encode(pdf_file.read()).decode('utf-8')
    return f"data:application/pdf;base64,{pdf_base64}"

def respond(message, chat_history, model, selected_pdf):
    # Check if the vector store for the selected PDF is already in the cache
    if selected_pdf not in vector_store_cache:
        chunks = chunk_processing(selected_pdf)
        vector_store = embeddings(chunks)
        vector_store_cache[selected_pdf] = vector_store  # Save the vector store in the cache
    else:
        vector_store = vector_store_cache[selected_pdf]
    
    # Create a combined history for context
    history_text = "\n".join([f"User: {m}\nBot: {r}" for m, r in chat_history])
    prompt_text = f"{history_text}\nUser: {message}\nBot:"

    response = generation_with_history(vector_store, prompt_text)
    response_text = response["result"]
    
    chat_history.append((message, response_text))
    save_chat_history(chat_history, selected_pdf)  # Save history
    
    return "", chat_history

def save_chat_history(chat_history, pdf_file):
    history_file = pdf_file + '.json'
    with open(history_file, 'w') as f:
        json.dump(chat_history, f)

def update_model(selected_model_name):
    global selected_model
    selected_model = selected_model_name
    return selected_model

def preload_vector_stores(uploaded_files, vector_store_cache):
    for file_path in uploaded_files:
        if file_path not in vector_store_cache:
            chunks = chunk_processing(file_path)
            vector_store = embeddings(chunks)
            vector_store_cache[file_path] = vector_store  # Save the vector store in the cache

# Preload vector stores for already uploaded files
preload_vector_stores(uploaded_files, vector_store_cache)

def upload_file(file):
    file_path = file.name
    uploaded_files.append(file_path)
    file_names = [get_file_name(f) for f in uploaded_files]

    # Process PDF and load into vector store
    if file_path not in vector_store_cache:
        chunks = chunk_processing(file_path)
        vector_store = embeddings(chunks)
        vector_store_cache[file_path] = vector_store  # Save the vector store in the cache

    pdf_base64 = load_pdf_to_base64(file_path)
    pdf_html = f'<iframe src="{pdf_base64}" width="100%" height="763px"></iframe>'
    
    return uploaded_files, gr.Dropdown(choices=file_names, value=get_file_name(file_path)), gr.HTML(value=pdf_html, visible=True), gr.update(interactive=True)

def sync_pdf_collection_shown(selected_file_name):
    return sync_dropdown(selected_file_name, uploaded_files)

theme = gr.themes.Monochrome(text_size="sm", primary_hue=gr.themes.colors.gray, secondary_hue=gr.themes.colors.indigo, font=[gr.themes.GoogleFont("Inconsolata"), "Arial", "sans-serif"])

with gr.Blocks(theme=theme, title="PDF Chatbot") as demo:

    with gr.Row():
        headline = gr.HTML(value="""
                            <h1 style='text-align: center; color: white; margin-top: 10px;'>
                                <span style='background: linear-gradient(to right, 
                                                #ff0000, #ff7f00, #ffff00, #00ff00, #00ffff, 
                                                #0000ff, #8b00ff, #ff00ff, #ff0000); 
                                                -webkit-background-clip: text; 
                                                -webkit-text-fill-color: transparent;'>
                                    YOLOPDF
                                </span>
                            </h1>

                            <h4 style='text-align: center; color: white; margin-top: 0px; margin-bottom: 5px'>
                                A Project by Jonathan, Walid and Mika
                            </h4>

                           """)
    with gr.Row():
        with gr.Column():  
            pdf_collection_dropdown = gr.Dropdown(choices=uploaded_files, label="PDF Collection Paths", show_label=True, interactive=True, visible=False)
            pdf_collection_dropdown_shown = gr.Dropdown(choices=[], label="PDF Collection", show_label=True, interactive=True)

        with gr.Column(): 
            dropdown = gr.Dropdown(models, label="LLM", show_label=True, value=models[0])
    with gr.Row():
        with gr.Column():        
            file_output = gr.File(visible=False)
            with gr.Group():
                upload_button = gr.UploadButton("Click to Upload a File", file_types=["pdf"], file_count="single", size="sm")
                pdf_view = gr.HTML(value="<p style='width: 100%; height: 763px; display: flex; align-items: center; justify-content: center; text-align: center; margin: 0; background-color: #262626;'>No PDF uploaded</p>", visible=True)
            
        with gr.Column():
            with gr.Group():
                with gr.Row():
                    download_json = gr.Button("Download JSON", visible=True, size="sm")  
                    clear = gr.Button("Clear", size="sm")
                chatbot = gr.Chatbot(height=632)
            msg = gr.Textbox(label="Enter your message", interactive=False) 

        
    pdf_collection_dropdown.change(change_pdf, pdf_collection_dropdown, [pdf_view, chatbot])
    pdf_collection_dropdown_shown.change(lambda x: sync_pdf_collection_shown(x), pdf_collection_dropdown_shown, pdf_collection_dropdown)
    dropdown.change(update_model, dropdown, None) 
    upload_button.upload(upload_file, upload_button, [file_output, pdf_collection_dropdown_shown, pdf_view, msg])
    msg.submit(respond, [msg, chatbot, dropdown, pdf_collection_dropdown], [msg, chatbot])
    clear.click(lambda: None, None, chatbot, queue=False)
    download_json.click(download_json_action, pdf_collection_dropdown)

demo.launch(share=False)
