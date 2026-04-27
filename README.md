# 🎓 AI-Powered Academic Success Tracker

<p align="center">
  <b>Enterprise-grade Educational Analytics Platform</b><br>
  Predict • Explain • Personalize • Improve
</p>

---

## 🚀 Overview

AI Academic Success Tracker leverages **Machine Learning + Generative AI** to:

- 📊 Predict student risk early  
- 🧠 Explain AI decisions transparently  
- 🤖 Generate personalized improvement plans  
- 🔐 Provide secure, role-based dashboards  

---

## ✨ Features

### 🧠 Predictive & Explainable AI
| Feature | Description |
|--------|------------|
| **XGBoost Engine** | Predicts student risk using 9 academic features |
| **SHAP Explainability** | Explains why a student is flagged |

---

### 🤖 Generative AI (Google Gemini 2.5)
| Feature | Description |
|--------|------------|
| **Student Action Plans** | AI-generated 3-step improvement strategies |
| **Automated Reports** | Executive summaries + mentor insights with PDF export |

---

### 🔐 Security
- JWT-based authentication (stateless & scalable)  
- Role-based dashboards:
  - 👨‍🎓 Students → Personal tracking  
  - 👩‍🏫 Educators → Cohort analytics  

---

### 📊 Visualization
- Interactive **Radar Chart Simulation** (What-if analysis)  
- Export data as **PDF / CSV reports**  

---

## 🛠️ Tech Stack

| Layer | Technology |
|------|------------|
| **Backend** | Python, Flask, Flask-JWT-Extended |
| **Frontend** | Vue.js 3, Chart.js, HTML5, CSS |
| **AI/ML** | XGBoost, SHAP, Google Gemini API |
| **Database** | SQLite3 |

---

## 📦 Installation & Setup

<details>
<summary><b>Click to expand</b></summary>

### 1️⃣ Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/AI-Academic-Success-Tracker.git
cd AI-Academic-Success-Tracker
2️⃣ Install Dependencies
pip install -r requirements.txt
3️⃣ Configure Environment Variables

Create a .env file in the root directory:

GEMINI_API_KEY=your_google_gemini_api_key_here
JWT_SECRET_KEY=your_ultra_secure_secret_key_here
4️⃣ Run the Application
python app.py
5️⃣ Access the App
http://127.0.0.1:5000
</details>
📋 Roadmap
✅ Machine Learning Model Integration
✅ JWT Authentication & Security
✅ Generative AI Report Generation
🔄 Floating AI Chatbot (Real-time Support)
🔄 Mobile App Optimization
👨‍💻 Author

Ananta Kishore Swain
Full Stack AI Developer / AI Engineer

GitHub: https://github.com/ananta12-d
LinkedIn: https://www.linkedin.com/in/ananta-kishore-swain-6282472bb/
📄 License

This project is licensed under the MIT License.
