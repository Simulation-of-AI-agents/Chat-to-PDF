---

# YOLOPDF - A PDF Chatbot

YOLOPDF is a project developed by Jonathan, Walid, and Mika for the "Simulation of AI Agents" class. This project demonstrates how AI can interact with PDF documents, extract relevant information, and facilitate user interaction through a chatbot interface.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
   - [Components](#components)
   - [Language Models Used](#language-models-used)
   - [Architecture Screenshot](#architecture-screenshot)
2. [Deployment Guide](#deployment-guide)
3. [Usage Instructions](#usage-instructions)
   - [Uploading and Processing PDFs](#uploading-and-processing-pdfs)
   - [Downloading JSON](#downloading-json)
4. [Project Review](#project-review)
   - [Features](#features)
   - [Development Process](#development-process)
5. [Course Improvement Suggestions](#course-improvement-suggestions)
6. [Additional Notes](#additional-notes)

---

## Architecture Overview

### Components

1. **Frontend (Gradio Interface)**
   - **PDF Viewer:** Displays the uploaded PDF within an HTML-iFrame.
   - **Chatbot Interface:** Provides a chat interface for user interaction with the PDF content.
   - **Model Selection:** Allows the selection of different language models (LLMs).
   - **File Upload and JSON Download:** Facilitates uploading PDFs and downloading extracted information in JSON format.

2. **Backend**
   - **PDF Processing:** Extracts text from uploaded PDFs and splits it into chunks.
   - **LLM Integration:** Utilizes `ChatOpenAI` and `HuggingFaceEmbeddings` for processing and generating responses.
   - **Vector Store:** Uses FAISS to store and retrieve text embeddings.
   - **Chat History:** Saves and loads chat history in JSON files.

### Language Models Used

1. **mixtral-8x7b-instruct**
2. **meta-llama-3-70b-instruct**
3. **qwen1.5-72b-chat**

These models are initialized with the `ChatOpenAI` class from the `langchain_openai` library and are optimized for tasks such as text extraction and question answering.

### Architecture Screenshot

![Architecture Screenshot](screenshots/architecture_screenshot.png)


---

## Deployment Guide

1. **Prerequisites**
   - Install the required libraries using:
   ```bash
   pip install -r requirements.txt
   ```

2. **Clone the repository**
   ```bash
   git clone https://github.com/username/yolopdf.git
   cd yolopdf
   ```

3. **Configure API Key**
   - Create a configuration file `Chatbot/key.secret`.
   - Add the following content with your API key:
     ```ini
     [GWDG]
     API_KEY=your_openai_api_key
     ```

4. **Start the application**
   ```bash
   python gradio-app.py
   ```


The Gradio interface will start locally and can be accessed through a web browser on port:

```bash
http://127.0.0.1:7860/
```

---

## Usage Instructions

### Uploading and Processing PDFs

1. **Upload PDF**
   - Click the "Click to Upload a File" button.
   - Select a PDF from your local filesystem.

2. **View and Interact with PDF**
   - The uploaded PDF will be displayed in the PDF viewer.
   - Use the dropdown menu to switch between multiple uploaded PDFs.

3. **Chatbot Interaction**
   - Enter your questions or commands in the message field and press Enter.
   - The chatbot will respond based on the PDF content and the previous chat history.

### Downloading JSON

- After processing a PDF, click the "Download JSON" button to download the extracted information in JSON format.
- The generated JSON files for the Sustainability Reports are located in the `extract` folder.

---

## Project Review

### Features

- **PDF Text Extraction:** Efficiently processes and extracts text from PDFs, including handling encrypted files.
- **Interactive Chatbot:** Enables natural language interaction with PDF contents through advanced language models.
- **JSON Export:** Provides a convenient way to download extracted information.

### Development Process

The project evolved through several phases:

1. **Initial Setup:** Basic integration with `gradio` and building the PDF processing pipeline.
2. **LLM Integration:** Experimenting with different LLMs to find the best solution for text extraction and response generation.
3. **UI/UX Enhancements:** Improving the user interface with features like file upload, dropdown menus, and JSON export.
4. **Optimization:** Fine-tuning chunk sizes and embedding strategies to enhance performance and accuracy.

---

## Course Improvement Suggestions

1. **More Practical Assignments:** Including more practical assignments focused on specific aspects of AI simulation would lead to better learning outcomes.
2. **Extended Deadlines for Complex Projects:** More time for complex projects like this would help students delve deeper into the subject matter.
3. **Collaborative Workshops:** Workshops where students collaborate and solve common problems would improve the learning experience.

---

## Additional Notes

- **Browser Recommendation:** Use Firefox or Safari, as larger PDFs may not display correctly in Chrome.
- **JSON Files:** The generated JSON files for the Sustainability Reports are located in the `extract` folder.

---

If you encounter issues or have questions, feel free to contact us via the issue tracker on the repository.
