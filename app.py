import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from pypdf import PdfReader
import docx
from google import genai
from google.genai import types

app = Flask(__name__)
# Enable CORS for Live Server
CORS(app)

# Initialize Gemini Client (uses GEMINI_API_KEY environment variable, or fallback key)
api_key = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6Jd5sVg3-hN2jORut-ihWFEC_ZXU5Z0hmOVI3WpRbfTAg")
client = genai.Client(api_key=api_key)

def extract_text_from_file(file_storage):
    filename = file_storage.filename.lower()
    text = ""
    try:
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
    except Exception as err:
        print(f"File extraction error: {err}")
    return text.strip()

@app.route("/api/analyze-resume", methods=["POST"])
def analyze_resume():
    if "resume" not in request.files:
        return jsonify({"error": "No resume file uploaded"}), 400

    file = request.files["resume"]
    if file.filename == "":
        return jsonify({"error": "Selected file is empty"}), 400

    extracted_text = extract_text_from_file(file)
    if not extracted_text:
        return jsonify({"error": "Could not extract readable text from document. Ensure it has selectable text."}), 400

    prompt = f"""
    You are an expert technical campus placement coach and recruiter.
    Analyze the following resume text extracted from a student candidate:

    --- RESUME TEXT ---
    {extracted_text}
    --- END RESUME TEXT ---

    Detect the candidate's career domain (e.g., Early Childhood Development, Full-Stack Engineering, Cloud & DevOps, Data Analytics, etc.).
    Extract the 4 most critical domain topics/skills for that career path and score them 0-100 based on the resume.

    Provide categorized improvement advice:
    - layout: 2-3 specific bullet formatting or impact phrasing suggestions.
    - concepts: 2-3 essential concepts or technologies they must learn.
    - projectsAndCerts: 2-3 portfolio projects or recognized credentials to pursue.

    Return a structured JSON object matching this exact schema:
    {{
        "domain": "Detected Domain Title",
        "score": "XX/100",
        "scoreNum": 80,
        "strengths": ["3 concise strengths"],
        "gaps": ["3 concise gaps"],
        "recommendations": {{
            "layout": ["2-3 bullet layout tips"],
            "concepts": ["2-3 concepts or tools to master"],
            "projectsAndCerts": ["2-3 projects or certifications"]
        }},
        "topicScores": [
            {{"topic": "Key Domain Subject 1", "score": 85}},
            {{"topic": "Key Domain Subject 2", "score": 75}},
            {{"topic": "Key Domain Subject 3", "score": 70}},
            {{"topic": "Key Domain Subject 4", "score": 80}}
        ]
    }}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        result_data = json.loads(response.text)
        result_data["fileName"] = file.filename
        return jsonify(result_data)

    except Exception as e:
        print("Backend analysis error:", e)
        return jsonify({"error": f"AI evaluation failed: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)