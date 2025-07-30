# 🧠 AI Notes Summarizer

An AI-powered web app that summarizes long text or uploaded `.txt` notes into short, readable summaries using the T5 model from Hugging Face Transformers.

<img width="1324" height="717" alt="Screenshot 2025-07-30 172103" src="https://github.com/user-attachments/assets/81e0c270-babe-4cfc-b574-f47a71fa97da" />


---

## 🚀 Features

- ✅ Paste text to get a smart AI summary
- 📄 Upload `.txt` files
- 🔊 Text-to-Speech for audio reading
- 🎙️ Speech-to-Text for your mic
- 💾 Download summary as `.txt`
- ⚡ Fast and responsive web interface
- 🤖 Powered by Hugging Face `t5-small` model 
- 🦹‍♂️ show more..
---

## 🛠️ Built With

- **Python**
- **Flask**
- **Hugging Face Transformers**
- **HTML/CSS/JS**
- **T5 Model**

---
## 📁 Folder Structure
```bash
ai-notes-summarizer/
│
├── app.py                       # Main Flask application
│
├── requirements.txt             # (optional) list of dependencies
│
├── README.md                    # Project description for GitHub
│
├── static/                      # All static files (CSS, images, JS)
│   ├── css/
│   │   └── style.css            # External CSS for styling the UI
│   │
│   └── assets/
│       └── logo.jpeg            # Favicon/logo image
│
├── templates/                   # HTML templates folder
│   └── index.html               # Main UI of the web app
│
└── uploads/                     # (optional) stores uploaded .txt files temporarily


```
---
## 💻 How to Run Locally

```bash
git clone https://github.com/yourusername/ai-notes-summarizer.git
cd ai-notes-summarizer

# Optional: create virtual environment
python -m venv venv
venv\Scripts\activate    # On Windows
# or
source venv/bin/activate # On Linux/Mac

# Install requirements
pip install flask transformers torch sentencepiece

# Run the app
python app.py
Open browser at http://127.0.0.1:5000
```
