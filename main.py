import os
from io import BytesIO

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from google import genai

from pypdf import PdfReader
from docx import Document
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(api_key=API_KEY)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Sumit Kumar AI Portfolio API",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# PORTFOLIO INFORMATION
# ============================================================

PORTFOLIO_CONTEXT = """
You are the AI assistant for Sumit Kumar's portfolio.

Sumit Kumar is a Computer Science undergraduate at VIT-AP
specializing in AI & ML.

Education:
- Bachelor of Technology in Computer Science
- Specialization: AI & ML
- VIT-AP University
- Expected graduation: 2027
- GPA: 8.28

Programming:
- Python
- Java

Data Analytics:
- Data Cleaning
- Data Preprocessing
- Database Management
- Exploratory Data Analysis (EDA)
- Data Visualization
- MS Excel
- Power BI
- SQL

AI / Machine Learning:
- Machine Learning
- Deep Learning
- NumPy
- Pandas
- Recommendation Systems
- LangChain
- Agentic AI
- LLMs
- Prompt Engineering
- RAG

Web / Development:
- React.js
- Node.js
- Express.js
- HTML
- CSS
- FastAPI

Cloud / Tools:
- AWS
- Git
- GitHub

Experience:
AI Research Intern at Coding Jr.
April 2025 - August 2025

During the internship Sumit:
- Researched enterprise AI copilots.
- Studied LLM architecture and applications.
- Explored prompt engineering.
- Explored Retrieval-Augmented Generation (RAG).
- Explored tool-calling mechanisms.
- Evaluated AI productivity tools including GitHub Copilot.

Project:
Customer Behaviour Analysis

Technologies:
Python, Pandas, SQL, Power BI.

Work included:
- Data cleaning
- Exploratory data analysis
- SQL business analysis
- Customer segmentation
- Product performance analysis
- Spending behavior analysis
- Purchase frequency analysis
- Interactive Power BI dashboard development

Certifications:
- Oracle OCI Foundation Associate
- Oracle AI Foundation Associate

Other:
- Event Leadership
- Team Management
- President of Madhya Bharat Association

Languages:
- English
- Hindi
"""


# ============================================================
# CHAT REQUEST MODEL
# ============================================================

class ChatRequest(BaseModel):
    question: str


# ============================================================
# HOME ROUTE
# ============================================================

@app.get("/")
def home():
    return FileResponse("frontend/index.html")

# ============================================================
# AI PORTFOLIO CHATBOT
# ============================================================

@app.post("/chat")
def chat(request: ChatRequest):

    prompt = f"""
You are Sumit Kumar's professional portfolio AI assistant.

Use ONLY the portfolio information provided below.

If the answer is not available in the portfolio information,
say that the information is not available.

Keep answers professional, clear and concise.

PORTFOLIO INFORMATION:
{PORTFOLIO_CONTEXT}

USER QUESTION:
{request.question}
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        return {
            "answer": response.text
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Gemini API error: {str(e)}"
        )


# ============================================================
# EXTRACT TEXT FROM PDF
# ============================================================

def extract_pdf_text(file_bytes: bytes) -> str:

    pdf_file = BytesIO(file_bytes)

    reader = PdfReader(pdf_file)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


# ============================================================
# EXTRACT TEXT FROM DOCX
# ============================================================

def extract_docx_text(file_bytes: bytes) -> str:

    doc_file = BytesIO(file_bytes)

    document = Document(doc_file)

    text = ""

    for paragraph in document.paragraphs:

        if paragraph.text.strip():
            text += paragraph.text + "\n"

    return text
def format_jd_answer(text: str) -> str:
    """
    Convert Gemini's JD analysis into clean HTML.
    """

    import re
    import html

    text = html.escape(text)

    # Remove markdown bold markers
    text = text.replace("**", "")

    # Convert section headings
    headings = [
        "MATCH SCORE:",
        "MATCHING SKILLS:",
        "MISSING / REQUIRED SKILLS:",
        "STRENGTHS:",
        "RECOMMENDATIONS:",
        "FINAL VERDICT:"
    ]

    for heading in headings:
        text = text.replace(
            heading,
            f'<div class="jd-heading">{heading.replace(":", "")}</div>'
        )

    # Convert bullet points
    text = re.sub(
        r'(?m)^-\s*(.+)$',
        r'<div class="jd-bullet">✓ \1</div>',
        text
    )

    # Convert percentage score
    text = re.sub(
        r'MATCH SCORE</div>\s*(\d+)%',
        r'MATCH SCORE</div><div class="jd-score">\1%</div>',
        text
    )

    # Convert line breaks
    text = text.replace("\n", "<br>")

    return text

# ============================================================
# JD MATCHER
# ============================================================

@app.post("/match-jd")
async def match_jd(file: UploadFile = File(...)):

    # --------------------------------------------------------
    # CHECK FILE TYPE
    # --------------------------------------------------------

    filename = file.filename.lower()

    if not (
        filename.endswith(".pdf")
        or filename.endswith(".docx")
    ):

        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported."
        )


    # --------------------------------------------------------
    # READ FILE
    # --------------------------------------------------------

    file_bytes = await file.read()


    # --------------------------------------------------------
    # EXTRACT TEXT
    # --------------------------------------------------------

    try:

        if filename.endswith(".pdf"):

            jd_text = extract_pdf_text(file_bytes)

        else:

            jd_text = extract_docx_text(file_bytes)

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=f"Could not read the file: {str(e)}"
        )


    # --------------------------------------------------------
    # CHECK TEXT
    # --------------------------------------------------------

    if not jd_text.strip():

        raise HTTPException(
            status_code=400,
            detail="Could not extract text from the uploaded file."
        )


    # --------------------------------------------------------
    # GEMINI PROMPT
    # --------------------------------------------------------

    prompt = f"""
You are an AI Job Description Matcher.

Analyze the following job description against Sumit Kumar's
portfolio.

Return a professional analysis using exactly this structure:

MATCH SCORE: <number>%

MATCHING SKILLS:
- skill
- skill
- skill

MISSING / REQUIRED SKILLS:
- skill
- skill
- skill

STRENGTHS:
- strength
- strength
- strength

RECOMMENDATIONS:
- recommendation
- recommendation
- recommendation

FINAL VERDICT:
<2-4 sentence professional conclusion>

Important:
- Do not invent skills that Sumit does not have.
- Base the analysis on the portfolio information.
- The match score should represent how closely Sumit's current
  skills and experience match the requirements of the JD.

SUMIT'S PORTFOLIO:
{PORTFOLIO_CONTEXT}

JOB DESCRIPTION:
{jd_text}
"""

    # --------------------------------------------------------
    # CALL GEMINI
    # --------------------------------------------------------

    try:

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        return {
    "filename": file.filename,
    "answer": format_jd_answer(response.text)
}

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Gemini API error: {str(e)}"
        )
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")