from flask import Flask, request, jsonify
from flask_cors import CORS
import pdfplumber
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = Flask(__name__)
CORS(app)

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

# Function to analyze resume with AI
def analyze_resume(resume_text, job_desc, prompt):
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(f"""
    {prompt}
    
    Resume:
    {resume_text}
    
    Job Description:
    {job_desc}
    """)
    return response.text

# Define Prompts
prompts = {
    "keypoints": "Extract technical skills, soft skills, education details, and experience/project information from the resume.",
    "match": "You are an experienced Technical Human Resource Manager,your task is to review the provided resume against the job description.",
    "missing_keywords": "Analyze a resume and job description. Identify keywords and skills from the job description absent in the resume.Prioritize based on frequency and relevance to the job. Provide suggestions for integrating these keywords into the resume,emphasizing achievements and quantifiable results.",
    "resume_score": "Analyze the resume against the job description and return only the match score (percentage)."
}

# Flask Routes
@app.route("/")
def home():
    return jsonify({"message": "Welcome to ATS Analyzer API! Use /analyze to process resumes."})
@app.route("/analyze", methods=["POST"])
def analyze():
    resume_file = request.files.get("resume")
    job_desc = request.form.get("job_desc")
    analysis_type = request.form.get("analysis_type")

    if not resume_file or not job_desc or not analysis_type:
        return jsonify({"error": "Missing required fields"}), 400

    resume_text = extract_text_from_pdf(resume_file)
    if not resume_text:
        return jsonify({"error": "Could not extract text from PDF"}), 400

    prompt = prompts.get(analysis_type)
    if not prompt:
        return jsonify({"error": "Invalid analysis type"}), 400

    analysis = analyze_resume(resume_text, job_desc, prompt)
    return jsonify({"result": analysis})

if __name__ == "__main__":
    app.run(debug=True)
