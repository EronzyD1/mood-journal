# 📝 Mood Journal – AI-Powered Emotion Tracker

Mood Journal is a simple yet powerful web app that helps users **track their emotions** through journaling.  
It uses **AI (Hugging Face Sentiment Analysis)** to analyze entries, stores them in a database, displays **mood trends with charts**, and supports **monetization with Flutterwave**.

---

## 🚀 How It Works
1. User writes a journal entry.
2. Flask backend sends the text to Hugging Face API → gets emotion scores (e.g., Happy: 85%).
3. Top emotion and score are stored in the database.
4. Chart.js on the frontend displays mood trends over time.
5. Users can upgrade to **PRO** via **Flutterwave payment** to unlock features:
   - Longer history  
   - CSV export  

---

## 🛠️ Tech Stack
- **Frontend**: HTML5, CSS, JavaScript, Chart.js  
- **Backend**: Python (Flask)  
- **Database**: SQLite (dev) / MySQL (prod)  
- **AI**: Hugging Face Sentiment Analysis API  
- **Payments**: Flutterwave Checkout  
- **Deployment**: (options: Replit, Render, Hugging Face Spaces, etc.)

---

## 💡 AI Prompts Used
We used AI tools like **ChatGPT, Cursor, Canva** to speed up development and design:

### **ChatGPT**
- *“Generate a Flask app with SQLite + Hugging Face API for emotion analysis.”*
- *“Fix IndentationError in my models.py.”*
- *“Add emoji display for emotions on the mood chart.”*
- *“Integrate Flutterwave payments in Flask app.”*

### **Cursor (AI code editor)**
- *“Refactor app.js to handle CSV export.”*
- *“Generate models.py with SQLAlchemy for User, Entry, Payment.”*

### **Canva**
- *“Create a pitch deck for Mood Journal – AI-powered emotion tracker, with slides for problem, solution, demo screenshots, and business model.”*

---

## 📦 Installation
Clone the repo and install dependencies:

\`\`\`bash
git clone https://github.com/<your-username>/mood-journal.git
cd mood-journal
pip install -r requirements.txt
\`\`\`

Set up environment variables in \`.env\`:

\`\`\`ini
FLASK_ENV=development
FLASK_SECRET_KEY=your_secret
APP_BASE_URL=http://localhost:5000
SQLALCHEMY_DATABASE_URI=sqlite:///mood_journal.db

HUGGINGFACE_API_KEY=hf_...
HUGGINGFACE_MODEL=j-hartmann/emotion-english-distilroberta-base

FLW_PUBLIC_KEY=FLWPUBK_TEST-...
FLW_SECRET_KEY=FLWSECK_TEST-...
FLW_WEBHOOK_SECRET=your_webhook_secret
SUBSCRIPTION_AMOUNT=2000
SUBSCRIPTION_CURRENCY=NGN
SUBSCRIPTION_DURATION_DAYS=365
\`\`\`

Run the app:
\`\`\`bash
python -m flask --app app.py run
\`\`\`

Visit 👉 \`http://127.0.0.1:5000\`

---

## 📊 Usage
- Write a journal entry → AI shows detected emotion.
- Mood trend appears on the chart.
- Save email + Pay with Flutterwave to unlock **PRO features**.
- Export your data as CSV (PRO only).

---

## 📈 Future Features
- Multi-user accounts with login  
- Dark mode UI  
- More advanced emotion models  
- Hosting on Render/Hugging Face Spaces  

---

## 👨‍💻 Contributors
Built with ❤️ using **ChatGPT**, **Cursor**, and **Canva** prompts.
