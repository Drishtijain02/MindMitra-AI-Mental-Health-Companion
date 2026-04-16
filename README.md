# 🧠 MindMitra – AI Mental Health Companion

An AI-powered journaling web application that analyzes user emotions and sentiment using Machine Learning and provides personalized, empathetic responses using Large Language Models (LLMs).

---

## 🚀 Overview

MindMitra is designed as a **mental wellness companion** that allows users to express their thoughts through journaling while receiving intelligent emotional insights and supportive responses.

The system combines:

* **Machine Learning models** for emotion & sentiment detection
* **LLM-based response generation** for empathetic interaction
* A clean and intuitive **full-stack web interface**

---

## 🧠 Key Features

* ✍️ **AI Journal System**
  Write daily thoughts and reflect freely in a safe digital space.

* 🔍 **Emotion Detection (ML Model)**
  Classifies user input into emotions such as *Happy, Sad, Stress, etc.*

* 📊 **Sentiment Analysis**
  Determines whether the journal entry is *Positive, Negative, or Neutral*

* 🤖 **AI-Generated Responses (LLM)**
  Provides supportive, human-like responses based on emotional context

* 📜 **Journal History Tracking**
  View past entries along with detected emotions and AI insights

* 💬 **Chat Section**
  Separate conversational interface for real-time interaction

---

## 🧠 Machine Learning Pipeline

The system uses a traditional NLP-based ML approach:

1. **Text Preprocessing**

   * Lowercasing
   * Cleaning & normalization

2. **Feature Extraction**

   * TF-IDF Vectorization

3. **Model Training**

   * Logistic Regression / Classification Model
   * Separate models for:

     * Emotion Classification
     * Sentiment Analysis

4. **Prediction Output**

   * Emotion label + confidence score
   * Sentiment label + confidence score

---

## 🤖 LLM Integration

The application integrates with an LLM (via OpenRouter) to:

* Generate empathetic responses
* Provide actionable suggestions
* Offer motivational and reflective insights

The ML output (emotion + sentiment) is used as **context for response generation**, creating a hybrid AI system.

---

## 🏗️ Tech Stack

### 🔹 Backend

* FastAPI
* Python
* Scikit-learn (ML models)
* OpenRouter API (LLM integration)

### 🔹 Frontend

* React (Vite)
* Tailwind CSS
* Axios

### 🔹 Data Storage

* Local JSON-based storage (for journal entries)

---

## 📁 Project Structure

```
MentalHealthAI/
├── Backend/
│   ├── main.py
│   ├── journal.json
│   └── ML + API logic
├── Frontend/
│   ├── src/
│   └── UI components
├── .gitignore
├── README.md
```

---

## ⚙️ How to Run Locally

### 1. Clone the Repository

```
git clone <your-repo-link>
cd MentalHealthAI
```

---

### 2. Backend Setup

```
cd Backend
pip install -r requirements.txt
uvicorn main:app --reload
```

---

### 3. Frontend Setup

```
cd Frontend
npm install
npm run dev
```

---

### 4. Open in Browser

```
http://localhost:5173
```

---

## 🔐 Environment Variables

Create a `.env` file and add:

```
OPENROUTER_API_KEY=your_api_key_here
```

---

## ⚠️ Note

This is a **demo version**.
Journal data is stored locally and is not encrypted.

---

## 🚀 Future Improvements

* 🔐 User Authentication (Login/Signup with JWT)
* 🔒 Data Encryption for privacy protection
* ☁️ Cloud Database Integration (MongoDB / Firebase)
* 📊 Mood Analytics Dashboard (graphs & trends)
* 🧠 Context-aware AI (RAG-based memory using past journals)
* 📱 Mobile responsiveness & PWA support

---

## 🎯 Project Highlights

* Combines **Machine Learning + LLMs** in a single system
* Demonstrates **real-world NLP application**
* Full-stack implementation with clean UI/UX
* Focus on **mental health and user experience**

---

<img width="1918" height="970" alt="image" src="https://github.com/user-attachments/assets/13d87c16-7d72-4224-8f76-2acaba510fad" />
<img width="1864" height="993" alt="image" src="https://github.com/user-attachments/assets/ebda467f-72e8-4077-bf75-729e6368ea33" />
<img width="1482" height="821" alt="image" src="https://github.com/user-attachments/assets/9ad7fdc1-a2ed-4f52-8266-e613d1f2adea" />
<img width="1380" height="976" alt="image" src="https://github.com/user-attachments/assets/3b7a1a49-4831-4c77-a586-b60688db3531" />





## 💡 Inspiration

Built to create a **safe and intelligent digital space** where users can reflect, express, and feel heard.

---

## 📌 Author

**Drishtii**

---

## ⭐ If you like this project

Give it a ⭐ on GitHub and share your feedback!
