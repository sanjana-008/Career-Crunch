import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from pypdf import PdfReader
import docx
from google import genai
from google.genai import types

from dotenv import load_dotenv
load_dotenv()

client = genai.Client()  # automatically reads GEMINI_API_KEY from the environment
app = Flask(__name__)
CORS(app)

# Explicitly pass your API key here
client = genai.Client(api_key="AQ.Ab8RN6Jd5sVg3-hN2jORut-ihWFEC_ZXU5Z0hmOVI3WpRbfTAg")

def extract_text_from_file(file_storage):
    filename = file_storage.filename.lower()
    text = ""
    
    if filename.endswith(".pdf"):
        reader = PdfReader(file_storage)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
                
    elif filename.endswith(".docx"):
        doc = docx.Document(file_storage)
        for para in doc.paragraphs:
            text += para.text + "\n"
            
    return text.strip()

@app.route("/api/analyze-resume", methods=["POST"])
def analyze_resume():
    if "resume" not in request.files:
        return jsonify({"error": "No resume file uploaded"}), 400

    file = request.files["resume"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    extracted_text = extract_text_from_file(file)
    if not extracted_text:
        return jsonify({"error": "Could not extract text. Check that the PDF has selectable text."}), 400

    prompt = f"""
    You are an expert career placement coach and industry recruiter.
    Analyze the following resume text:

    --- RESUME TEXT ---
    {extracted_text}
    --- END RESUME TEXT ---

    Detect the candidate's core domain/career field (e.g., Software Engineering, Childcare & Education, Data Science, Marketing, etc.).
    Extract the 4 most critical domain skills or subject areas expected for THAT career field, and evaluate the candidate's mastery in each based on their resume.

    Evaluate the resume thoroughly and provide a structured JSON response matching this exact schema:
    {{
        "domain": "Detected primary domain/role name",
        "score": "XX/100",
        "scoreNum": 80,
        "strengths": ["3 concise strengths"],
        "gaps": ["3 specific missing skills or project weaknesses"],
        "recommendations": ["3 actionable next steps"],
        "topicScores": [
            {{"topic": "Relevant Skill/Subject 1", "score": 85}},
            {{"topic": "Relevant Skill/Subject 2", "score": 70}},
            {{"topic": "Relevant Skill/Subject 3", "score": 60}},
            {{"topic": "Relevant Skill/Subject 4", "score": 90}}
        ]
    }}
    Return ONLY pure JSON.
    """

    try:
        # Change model to gemini-3.6-flash
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        result_data = json.loads(response.text)
        result_data["fileName"] = file.filename
        return jsonify(result_data)

    except Exception as e:
        print("Backend error trace:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)