# AI Grant Writer Assistant 🤖📄

An Agentic AI-powered web application that automates the end-to-end grant writing process for startups and NGOs.

This system uses multiple AI agents to:
- Discover relevant grant opportunities
- Validate eligibility requirements
- Generate structured, professional grant proposal reports

---

## 🔍 Problem Statement

Grant writing is complex, time-consuming, and requires strong research and writing skills.  
Many startups and NGOs struggle to:
- Find suitable funding programs  
- Understand eligibility rules  
- Write professional proposals that meet funder expectations  

---

## 🚀 Solution

AI Grant Writer Assistant solves this problem using **Agentic AI architecture**, where multiple specialized AI agents collaborate to complete the entire workflow automatically.

### AI Agents:
- **Research Agent** – Finds active grant opportunities  
- **Validation Agent** – Checks eligibility and risk factors  
- **Writer Agent** – Generates funder-ready proposal reports  

---

## 🛠 Tech Stack

- Python  
- CrewAI (Agent orchestration)  
- Groq (LLaMA 3.3)  
- Gemini 2.5 Flash  
- Flask  
- HTML / CSS / JavaScript  

---

## ✨ Key Features

- Multi-agent AI workflow  
- Real-time grant discovery using web search  
- Automatic eligibility validation  
- Professional Markdown proposal generation  
- Flask-based web interface  
- Downloadable grant strategy report  

---

## ☁️ Deploy to Vercel

This repository can be deployed as a Flask application on Vercel.

### 1. Import the repository
1. Open the [Vercel dashboard](https://vercel.com/new).
2. Import `antalaraj/AI-Grant-Writer-Assistant` from GitHub.
3. Use the repository root as the project root. Vercel detects the Flask entry point in `app.py`.

### 2. Add environment variables
In **Project Settings → Environment Variables**, add both API keys for Preview and Production as appropriate:

- `GROQ_API_KEY` — your Groq API key
- `GEMINI_API_KEY` — your Gemini API key

Optionally add `FLASK_SECRET_KEY` as a long random secret. Do not commit API keys to GitHub or expose them in frontend JavaScript.

### 3. Deploy
Deploy the project from Vercel. The included `vercel.json` sets a 300-second function duration; a workflow can still time out if it exceeds the maximum duration permitted by the selected Vercel plan and compute configuration.

### Deployment notes
- The Flask frontend and server-side workflow run as a Python application; frontend assets are served from `public/`.
- Grant reports are returned in the HTTP response. The deployed function should not be treated as persistent storage for generated files.
- Check Vercel's function logs if report generation fails. The workflow calls Groq, Gemini, and DuckDuckGo search services, so their API availability and rate limits can affect requests.
- The project has not been verified with a live Vercel deployment as part of these source changes.

## 🧪 How to Run Locally

### 1. Clone the repository
git clone https://github.com/antalaraj/AI-Grant-Writer-Assistant.git  
cd AI-Grant-Writer-Assistant   

### 2. Set API keys (Windows)
set GROQ_API_KEY=your_key_here  
set GEMINI_API_KEY=your_key_here  

### 3. Run the application
python web.py  

Open in browser:  
http://127.0.0.1:5000  

---

## 📊 System Workflow

1. User enters organization type and mission  
2. Research Agent finds relevant grants  
3. Validation Agent checks eligibility  
4. Writer Agent generates proposal  
5. Final report is displayed in web UI  

---

## 📁 Project Structure

```text
AI-Grant-Writer-Assistant/
├── app.py
├── web.py
│
├── templates/
│   ├── index.html
│   ├── loading.html
│   └── result.html
│
└── static/
    ├── css/
    └── js/
```

---

## 👨‍💻 Author
Raj Antala  
🎓 PGDM Student in AI and Data Science  
🏫 Adani Institute of Digital Technology Management (AIDTM)  
📍 Gandhinagar, India  
📧 antalaraj214@gmail.com  
🔗 www.linkedin.com/in/antalaraj

Passionate about building intelligent systems and real-world AI applications.

---

## 📌 Disclaimer

This project is built for educational and demonstration purposes.  
Users must provide their own API keys to run the system.
