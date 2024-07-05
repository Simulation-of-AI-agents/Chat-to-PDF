import os
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

# Read API key from config file
config = configparser.ConfigParser()
config_file_path = 'Chatbot/key.secret'
config.read(config_file_path)
api_key = config['GWDG']['API_KEY']

# Base URL for the API
base_url = "https://chat-ai.academiccloud.de/v1"

# List of available models (Intel model excluded due to bad performance)
models = ["mixtral-8x7b-instruct", "meta-llama-3-70b-instruct", "qwen1.5-72b-chat"]

uploaded_files = []
vector_store_cache = {}
selected_model = models[1]


def initialize_model(model_name):
    """
    Initialize ChatOpenAI model.

    Args:
        model_name (str): Name of the GDWG model to initialize.

    Returns:
        ChatOpenAI: Initialized ChatOpenAI model instance.
    """
    return ChatOpenAI(model_name=model_name, openai_api_key=api_key, openai_api_base=base_url, temperature=0)

# Initialize the model with the selected model name
model = initialize_model(selected_model)

def get_file_name(file_path):
    """
    Get the base name of a file from its path.

    Args:
        file_path (str): Path of the file.

    Returns:
        str: Base name of the file.
    """
    return os.path.basename(file_path)

def sync_dropdown(selected_file_name, all_files):
    """
    Synchronize PDF path dropdown with the PDF name dropdown.
    
    Args:
        selected_file_name (str): Selected file name.
        all_files (list): List of all file paths.

    Returns:
        str: File path corresponding to the selected file name.
    """
    for file in all_files:
        if get_file_name(file) == selected_file_name:
            return file
    return ""

def change_pdf(value):
    """
    Process PDF file and update the PDF view.

    Args:
        value (str): Path to the PDF file.

    Returns:
        tuple: HTML content and chat history.
    """
    pdf_base64 = load_pdf_to_base64(value)
    pdf_html = f'<iframe src="{pdf_base64}" width="100%" height="763px"></iframe>'
    chat_history = load_chat_history(value)
    return pdf_html, chat_history

def chunk_processing(pdf):
    """
    Split PDF into smaller text chunks. The size of the text chunks was tested individually for each model. Potentially encrypted PDFs are decrypted.

    Args:
        pdf (str): Path to the PDF file.

    Returns:
        list: List of text chunks.
    """
    try:
        pdf_reader = PyPDF2.PdfReader(pdf)
    except PyPDF2.errors.DependencyError:
        print("Error: PyCryptodome is required to process this PDF file.")
        return []

    if pdf_reader.is_encrypted:
        try:
            pdf_reader.decrypt("")  # Attempt to decrypt the PDF without password
        except:
            print("Error: Encrypted PDF file cannot be read.")
            return []

    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()

    # Adjust chunk size based on selected model
    chunk_size = 1000 if selected_model == "qwen1.5-72b-chat" else 2000
    chunk_overlap = chunk_size // 10

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    return text_splitter.split_text(text=text)

def download_json_action(pdf_file):
    """
    Performs a JSON download action for the selected PDF file. Uses individual prompts for each value to be searched for from the context text.

    Args:
        pdf_file (str): Path to the PDF file.

    Returns:
        str: Path to the downloaded JSON file.
    """
    # Print message to indicate JSON download is in progress
    print("\n" * os.get_terminal_size().lines,
          "Downloading JSON...",
          "\n" * (os.get_terminal_size().lines - 2))

    # Process PDF into chunks if not cached already
    if pdf_file not in vector_store_cache:
        chunks = chunk_processing(pdf_file)
        vector_store_cache[pdf_file] = embeddings(chunks)

    vector_store = vector_store_cache[pdf_file]

    # Define prompts for value extraction
    questions = {
        "CO2": "Answer this question with ONLY a single float value and NO refined Answer: What is the latest CO2 emissions in tons/annum? IMPORTANT: The number is explicitly mentioned in the report!",
        "NOX": "Answer this question with ONLY a single float value and NO refined Answer: What is the latest NOX emissions in tons/annum?",
        "Number_of_Electric_Vehicles": "Answer this question with ONLY a single integer value, NO WORDS OR DIGITS: How many electric vehicles are mentioned? (if not mentioned in the text write '0')",
        "Impact": "Summarize the negative impact on climate change addressed in the report. IMPORTANT: Answer in min 20 and max 50 Words",
        "Risks": "What are the material risks related to climate change? IMPORTANT: Answer in min 20 and max 50 Words",
        "Opportunities": "Summarize the financial materiality related to climate change. IMPORTANT: Answer in min 20 and max 50 Words",
        "Strategy": "Describe the company's strategy and business model for a sustainable economy. IMPORTANT: Answer in min 20 and max 50 Words",
        "Actions": "What actions and resources are mentioned in relation to sustainability? IMPORTANT: Answer in min 20 and max 50 Words",
        "Adopted_policies": "What policies has the company adopted for sustainability? IMPORTANT: Answer in min 20 and max 50 Words",
        "Targets": "What are the company's goals for a sustainable economy? IMPORTANT: Answer in min 20 and max 50 Words"
    }

    # saving file name as value in JSON file
    results = {"name": os.path.basename(pdf_file)}

    # Extract information based on predefined questions
    for key, question in questions.items():
        results[key] = extract_information(vector_store, question)

    # Create directory for JSON output if it doesn't exist
    output_dir = 'extract'
    os.makedirs(output_dir, exist_ok=True)

    json_file_name = os.path.splitext(os.path.basename(pdf_file))[0] + ".json"
    json_file_path = os.path.join(output_dir, json_file_name)

    # Write results to JSON file
    with open(json_file_path, 'w') as f:
        json.dump(results, f, indent=4, sort_keys=False)

    # Print message to indicate JSON download is complete
    print("\n" * os.get_terminal_size().lines,
          "JSON successfully downloaded!",
          "\n" * (os.get_terminal_size().lines - 2))

    return json_file_path

def extract_information(vector_store, question):
    """
    Extract information from vector store based on a question.

    Args:
        vector_store (FAISS): Vector store containing text embeddings.
        question (str): Question to be answered based on the vector store.

    Returns:
        str: Extracted information based on the question.
    """
    retriever = vector_store.as_retriever()
    model = initialize_model(selected_model)
    qa = RetrievalQA.from_chain_type(llm=model, chain_type="stuff", retriever=retriever, return_source_documents=False)
    result = qa.invoke(f"Extract information, but ONLY ANSWER THE QUESTION IF ITS MENTIONED IN THE RETRIEVED CONTEXT: {question}")
    return result["result"] if result else "Value not found"

def embeddings(chunks):
    """
    Generate embeddings from text chunks using local HuggingFaceEmbedding model.

    Args:
        chunks (list): List of text chunks.

    Returns:
        FAISS: Vector store containing embeddings.
    """
    embeddings_model_name = "sentence-transformers/all-MiniLM-L6-v2"
    embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)
    return FAISS.from_texts(chunks, embedding=embeddings)

def extract_text_from_pdf(path_file: str):
    """
    Extract text from a PDF file using PyPDF2.

    Args:
        path_file (str): Path to the PDF file.

    Returns:
        str: Extracted text from the PDF.
    """
    with open(path_file, 'rb') as pdf:
        reader = PyPDF2.PdfReader(pdf, strict=False)
        pdf_text = [page.extract_text() for page in reader.pages]
        return "".join(pdf_text)

def generation_with_history(vector_store, prompt_text):
    """
    Generate a ChatBot response based on the selected file with chat history.

    Args:
        vector_store (FAISS): Vector store containing text embeddings.
        prompt_text (str): Prompt text for generating the response.

    Returns:
        dict: Generated response.
    """
    retriever = vector_store.as_retriever()
    qa = RetrievalQA.from_chain_type(llm=model, chain_type="refine", retriever=retriever, return_source_documents=False)
    result = qa.invoke(f"Answer with Minimum 100 characters:{prompt_text}")
    return result

def load_chat_history(pdf_file):
    """
    Load chat history from a JSON file.

    Args:
        pdf_file (str): Path to the PDF file.

    Returns:
        list: Loaded chat history.
    """
    history_file = pdf_file + '.json'
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            return json.load(f)
    return []

def load_pdf_to_base64(pdf_path):
    """
    Load a PDF file and encode it to base64 for PDF view.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        str: Base64 encoded PDF data URI.
    """
    with open(pdf_path, "rb") as pdf_file:
        pdf_base64 = base64.b64encode(pdf_file.read()).decode('utf-8')
    return f"data:application/pdf;base64,{pdf_base64}"

# Function to respond to user input
def respond(message, chat_history, selected_pdf):
    """
    Respond to user input and update chat history.

    Args:
        message (str): User input message.
        chat_history (list): List of tuples containing chat history.
        selected_pdf (str): Path to the selected PDF file.

    Returns:
        tuple: Empty string and updated chat history.
    """
    # Process PDF file into chunks if not cached already
    if selected_pdf not in vector_store_cache:
        chunks = chunk_processing(selected_pdf)
        vector_store = embeddings(chunks)
        vector_store_cache[selected_pdf] = vector_store
    else:
        vector_store = vector_store_cache[selected_pdf]

    # Construct prompt text including chat history and user message
    history_text = "\n".join([f"User: {m}\nBot: {r}" for m, r in chat_history])
    prompt_text = f"{history_text}\nUser: {message}\nBot:"

    # Generate response with chat history
    response = generation_with_history(vector_store, prompt_text)
    response_text = response["result"]

    # Append user message and response to chat history
    chat_history.append((message, response_text))
    save_chat_history(chat_history, selected_pdf)

    return "", chat_history

def save_chat_history(chat_history, pdf_file):
    """
    Save chat history to a JSON file.

    Args:
        chat_history (list): List of tuples containing chat history.
        pdf_file (str): Path to the PDF file.
    """
    history_file = pdf_file + '.json'
    with open(history_file, 'w') as f:
        json.dump(chat_history, f)

def update_model(selected_model_name):
    """
    Update the selected model.

    Args:
        selected_model_name (str): Name of the selected model.

    Returns:
        str: Updated selected model name.
    """
    global selected_model, model
    if selected_model_name != selected_model:
        selected_model = selected_model_name
        model = initialize_model(selected_model_name)
    return selected_model

def preload_vector_stores(uploaded_files, vector_store_cache):
    """
    Preload vector stores for uploaded files.

    Args:
        uploaded_files (list): List of uploaded file paths.
        vector_store_cache (dict): Dictionary to cache vector stores.
    """
    for file_path in uploaded_files:
        if file_path not in vector_store_cache:
            chunks = chunk_processing(file_path)
            vector_store = embeddings(chunks)
            vector_store_cache[file_path] = vector_store

# Preload vector stores for uploaded files
preload_vector_stores(uploaded_files, vector_store_cache)

def upload_file(file):
    """
    Upload a PDF file.

    Args:
        file (File): Uploaded file object.

    Returns:
        tuple: Updated list of uploaded files, dropdown choices, HTML content for PDF view, and interactive update.
    """
    file_path = file.name
    uploaded_files.append(file_path)
    file_names = [get_file_name(f) for f in uploaded_files]

    # Process PDF file into chunks if not cached already
    if file_path not in vector_store_cache:
        chunks = chunk_processing(file_path)
        vector_store = embeddings(chunks)
        vector_store_cache[file_path] = vector_store

    # Generate base64 encoded PDF data URI for HTML display
    pdf_base64 = load_pdf_to_base64(file_path)
    pdf_html = f'<iframe src="{pdf_base64}" width="100%" height="763px"></iframe>'

    return uploaded_files, gr.Dropdown(choices=file_names, value=get_file_name(file_path)), gr.HTML(value=pdf_html, visible=True), gr.update(interactive=True)

def sync_pdf_collection_shown(selected_file_name):
    """
    Synchronize PDF collection dropdown.

    Args:
        selected_file_name (str): Selected file name.

    Returns:
        str: Synchronized PDF file path.
    """
    return sync_dropdown(selected_file_name, uploaded_files)

# Define Gradio theme
theme = gr.themes.Monochrome(text_size="sm", primary_hue=gr.themes.colors.gray, secondary_hue=gr.themes.colors.indigo, font=[gr.themes.GoogleFont("Inconsolata"), "Arial", "sans-serif"])

# Create Gradio interface
with gr.Blocks(theme=theme, title="PDF Chatbot") as demo:

    with gr.Row():
        # Headline for the chatbot interface in rainbow colors
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
            # Dropdown for selecting PDF files 
            pdf_collection_dropdown = gr.Dropdown(choices=uploaded_files, label="PDF Collection Paths", show_label=True, interactive=True, visible=False)
            pdf_collection_dropdown_shown = gr.Dropdown(choices=[], label="PDF Collection", show_label=True, interactive=True, visible=True)

        with gr.Column():
            # Dropdown for selecting LLM model
            dropdown = gr.Dropdown(models, label="LLM", show_label=True, value=selected_model)
    with gr.Row():
        with gr.Column():
            # File upload and display PDF in HTML iFrame
            file_output = gr.File(visible=False)
            with gr.Group():
                upload_button = gr.UploadButton("Click to Upload a File", file_types=["pdf"], file_count="single", size="sm")
                pdf_view = gr.HTML(value="<p style='width: 100%; height: 763px; display: flex; align-items: center; justify-content: center; text-align: center; margin: 0; background-color: #262626;'>No PDF uploaded</p>", visible=True)

        with gr.Column():
            # Chatbot interface with JSON download button, clear button, Chat interface and Message box
            with gr.Group():
                with gr.Row():
                    download_json = gr.Button("Download JSON", visible=True, size="sm")
                    clear = gr.Button("Clear", size="sm")
                chatbot = gr.Chatbot(height=632)
            msg = gr.Textbox(label="Enter your message", interactive=False)

    # Set up Gradio action callbacks
    pdf_collection_dropdown.change(change_pdf, pdf_collection_dropdown, [pdf_view, chatbot])
    pdf_collection_dropdown_shown.change(lambda x: sync_pdf_collection_shown(x), pdf_collection_dropdown_shown, pdf_collection_dropdown)
    dropdown.change(update_model, dropdown, None)
    upload_button.upload(upload_file, upload_button, [file_output, pdf_collection_dropdown_shown, pdf_view, msg])
    msg.submit(respond, [msg, chatbot, pdf_collection_dropdown], [msg, chatbot])
    clear.click(lambda: None, None, chatbot, queue=False)
    download_json.click(download_json_action, pdf_collection_dropdown)

# Launch Gradio interface
demo.launch(share=False)
