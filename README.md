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

## 🧪 How to Run Locally

### 1. Clone the repository
git clone https://github.com/antalaraj/AI-Grant-Writer-Assistant.git  
cd AI-Grant-Writer-Assistant  

### 2. Install dependencies
pip install -r requirements.txt  

### 3. Set API keys (Windows)
set GROQ_API_KEY=your_key_here  
set GEMINI_API_KEY=your_key_here  

### 4. Run the application
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
PGDM Student – AI & Data Science  
Adani Institute of Digital Technology Management (AIDTM)  

Passionate about building intelligent systems and real-world AI applications.

---

## 📌 Disclaimer

This project is built for educational and demonstration purposes.  
Users must provide their own API keys to run the system.
