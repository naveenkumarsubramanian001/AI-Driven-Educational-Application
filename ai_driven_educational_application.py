# -*- coding: utf-8 -*-
"""AI-driven educational application

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1J4s2NRYrmL3LpGUYMoG0538CCyQlDGfW
"""

from google.colab import files
from IPython.display import Video
!pip install -q git+https://github.com/openai/whisper.git
!sudo apt-get install -y ffmpeg
import whisper
!pip install -q sentence-transformers
pip install -U bitsandbytes
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from sentence_transformers import SentenceTransformer, util
from huggingface_hub import notebook_login
import requests
import json
from bs4 import BeautifulSoup
import re
!pip install fpdf
from fpdf import FPDF

from google.colab import files
from IPython.display import Video

# Upload video file
print("Please upload your lecture video file (e.g., .mp4, .mov):")
uploaded_files = files.upload()

# Get the uploaded file name
for filename in uploaded_files.keys():
    video_file = filename
    break

# Display the uploaded video
print(f"\nUploaded video: {video_file}")
Video(video_file, embed=True)

# Install Whisper and dependencies
!pip install -q git+https://github.com/openai/whisper.git
!sudo apt-get install -y ffmpeg

import whisper

# Load Whisper model (you can use "base", "small", "medium", or "large")
model = whisper.load_model("base")

# Replace with the name of your uploaded video file from Step 1
video_path = video_file  # This should be defined from Step 1

# Transcribe video to text
result = model.transcribe(video_path)
transcribed_text = result['text']

# Show transcribed text
print("\n--- TRANSCRIBED TEXT ---\n")
print(transcribed_text[:1000])  # Print first 1000 characters

# Log in to Hugging Face to access gated models
notebook_login()

model_name = "mistralai/Mistral-7B-Instruct-v0.1"  # or try: "tiiuae/falcon-7b-instruct"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",
)

text_gen = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=50)

def get_main_topic_from_llm(transcribed_text):
    prompt = f"""
### Instruction:
Given the transcript of a lecture, summarize the **main topic** in 1-3 words only. Do not include subtopics or extra explanation.

### Transcript:
{transcribed_text[:2000]}  # limit input for performance

### Main Topic:
"""
    result = text_gen(prompt, do_sample=False)[0]['generated_text']

    # Extract only the answer part
    topic_answer = result.split("### Main Topic:")[-1].strip().split("\n")[0]
    return topic_answer

main_topic = get_main_topic_from_llm(transcribed_text)
print("📌 Main Topic (LLM):", main_topic)

# Load a small, fast embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Your extracted main topic from LLM
main_topic = "Machine Learning"

# Predefined reference topics
reference_links = {
    "Supervised Learning": "https://en.wikipedia.org/wiki/Supervised_learning",
    "Unsupervised Learning": "https://en.wikipedia.org/wiki/Unsupervised_learning",
    "Neural Networks": "https://en.wikipedia.org/wiki/Artificial_neural_network",
    "Decision Trees": "https://en.wikipedia.org/wiki/Decision_tree",
    "Support Vector Machine": "https://en.wikipedia.org/wiki/Support_vector_machine",
    "Regression Models": "https://en.wikipedia.org/wiki/Regression_analysis",
    "Classification": "https://en.wikipedia.org/wiki/Statistical_classification",
    "Clustering": "https://en.wikipedia.org/wiki/Cluster_analysis",
    "Deep Learning": "https://en.wikipedia.org/wiki/Deep_learning",
    "Machine Learning": "https://en.wikipedia.org/wiki/Machine_learning"
}

# Encode main topic and reference topics
main_embedding = model.encode(main_topic, convert_to_tensor=True)
ref_embeddings = model.encode(list(reference_links.keys()), convert_to_tensor=True)

# Compute cosine similarities
cos_scores = util.cos_sim(main_embedding, ref_embeddings)[0]

# Get the best matching topic
best_match_idx = cos_scores.argmax().item()
best_topic = list(reference_links.keys())[best_match_idx]
best_link = reference_links[best_topic]

# Output
print("✅ Matched Topic:", best_topic)
print("🔗 Reference Link:", best_link)

!pip install -q requests beautifulsoup4

def get_text_from_url(url, max_paragraphs=15):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        paragraphs = soup.find_all('p')
        text = "\n\n".join(p.get_text().strip() for p in paragraphs[:max_paragraphs] if p.get_text().strip())

        # Remove citation markers like [1], [2], etc.
        clean_text = re.sub(r'\[\d+\]', '', text)
        return clean_text if clean_text else "No readable text found."

    except Exception as e:
        return f"Error fetching content: {e}"

reference_text = get_text_from_url(best_link)

print("\n--- Extracted Reference Text ---\n")
print(reference_text[:1500])  # Preview first 1500 characters

# Your Groq API key (⚠️ Keep this secret in production)
api_key = "--------------------------"

# Truncate inputs to fit within token limits
lecture_text = transcribed_text
reference_text_chunk = reference_text[:1500]

# Prepare prompt for study material generation
study_prompt = f"""
You are a teaching assistant. Generate a detailed, clear, and student-friendly study material using the given lecture transcription and reference content.

Lecture:
\"\"\"{lecture_text}\"\"\"

Reference:
\"\"\"{reference_text_chunk}\"\"\"

The content should be educational, well-structured with headers, and cover all major points explained in both sources.
"""

# Groq API endpoint
url = "https://api.groq.com/openai/v1/chat/completions"

# Payload for the request
payload = {
    "model": "meta-llama/llama-4-scout-17b-16e-instruct",
    "messages": [
        {
            "role": "user",
            "content": study_prompt
        }
    ],
    "temperature": 0.7
}

# Headers with API Key
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

# Send request to Groq
response = requests.post(url, headers=headers, data=json.dumps(payload))

# Get and display the result
if response.status_code == 200:
    result = response.json()
    study_material = result["choices"][0]["message"]["content"]
    print("✅ --- Study Material ---\n")
    print(study_material[:4000])  # Print first part
else:
    print("❌ Error:", response.status_code, response.text)

def save_to_pdf(text, filename="Study_Material.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line)

    pdf.output(filename)

save_to_pdf(study_material)
print("📄 Saved as: Study_Material.pdf")

