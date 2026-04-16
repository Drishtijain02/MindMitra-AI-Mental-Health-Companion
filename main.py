from fastapi import FastAPI
from pydantic import BaseModel
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JOURNAL_FILE = os.path.join(BASE_DIR, "journal.json")
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
JOURNAL_PATH = BASE_DIR / "journal.json"
from dotenv import load_dotenv
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENAI_API_KEY = ""
OPENROUTER_MODEL = "openai/gpt-3.5-turbo"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

app = FastAPI()
def predict_emotion(user_text, sentiment_model, emotion_model):
    """Predict sentiment, emotion, and model confidence from user journal text."""
    clean_text = preprocess_text(user_text)
    sentiment, sentiment_confidence = _highest_probability(sentiment_model, clean_text)
    emotion, emotion_confidence = _highest_probability(emotion_model, clean_text)

    return {
        "clean_text": clean_text,
        "sentiment": sentiment,
        "sentiment_confidence": sentiment_confidence,
        "emotion": emotion,
        "emotion_confidence": emotion_confidence,
    }
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
PROJECT_DIR = Path(".")
SUPPORTED_EMOTIONS = ["Happy", "Sad", "Stress", "Anxiety"]
SUPPORTED_SENTIMENTS = ["Positive", "Negative", "Neutral"]

SAMPLE_DATA = [
    ("I feel happy", "Positive", "Happy"),
    ("I feel sad", "Negative", "Sad"),
    ("I am stressed", "Negative", "Stress"),
    ("I feel anxious", "Negative", "Anxiety"),
]
FALLBACK_RESPONSES = {
    "Happy": {
        "supportive_response": "It's great that you're feeling positive.",
        "suggestion": "Take a moment to enjoy this feeling.",
        "motivation": "Keep doing what brings you joy."
    },
    "Sad": {
        "supportive_response": "I'm sorry you're feeling this way.",
        "suggestion": "Try talking to someone you trust.",
        "motivation": "This feeling will pass."
    },
    "Stress": {
        "supportive_response": "It sounds like things feel overwhelming.",
        "suggestion": "Take a short break and breathe deeply.",
        "motivation": "You can handle this step by step."
    },
    "Anxiety": {
        "supportive_response": "It’s okay to feel anxious sometimes.",
        "suggestion": "Focus on slow breathing.",
        "motivation": "You are safe right now."
    }
}
MOOD_SUPPORT = {
    "Sad": {
        "tip": "Try writing down what’s bothering you in detail.",
        "activity": "Listen to calming music or talk to a close friend.",
        "video": "https://www.youtube.com/watch?v=2OEL4P1Rz04"
    },
    "Stress": {
        "tip": "Take a 5-minute break and focus on breathing.",
        "activity": "Go for a short walk or stretch your body.",
        "video": "https://www.youtube.com/watch?v=1vx8iUvfyCY"
    },
    "Anxiety": {
        "tip": "Try the 4-7-8 breathing technique.",
        "activity": "Ground yourself by naming 5 things you see.",
        "video": "https://www.youtube.com/watch?v=O-6f5wQXSu8"
    },
    "Happy": {
        "tip": "Capture this moment in your journal.",
        "activity": "Share your happiness with someone.",
        "video": "https://www.youtube.com/watch?v=ZbZSe6N_BXs"
    }
}
HELPLINES = {
    "India": [
        {"name": "Kiran", "number": "1800-599-0019"},
        {"name": "AASRA", "number": "+91-9820466726"},
        {"name": "iCall", "number": "+91-9152987821"}
    ]
}
def generate_llm_response(user_text, emotion, sentiment, provider="OpenRouter only", api_key=None, model_name=None):
    """Generate an LLM response with Gemini/OpenAI/OpenRouter support and a safe fallback."""
    if provider == "Fallback only":
        return _fallback_response(emotion)

    prompt = _build_prompt(user_text, emotion, sentiment)
    key = (api_key or "").strip()

    try:
        if provider == "Google Gemini":
            key = key or GEMINI_API_KEY.strip()
            if not key or key == "YOUR_API_KEY_HERE":
                raise ValueError("Gemini API key is missing.")

            import google.generativeai as genai

            genai.configure(api_key=key)
            model = genai.GenerativeModel(GEMINI_MODEL)
            llm_result = model.generate_content(prompt)
            parsed = _parse_llm_text(llm_result.text, emotion)
            parsed["source"] = "Google Gemini"
            parsed["api_error"] = ""
            return parsed

        if provider == "OpenAI":
            key = key or OPENAI_API_KEY.strip()
            if not key or key == "YOUR_API_KEY_HERE":
                raise ValueError("OpenAI API key is missing.")

            from openai import OpenAI

            client = OpenAI(api_key=key)
            selected_model = model_name or OPENAI_MODEL
            try:
                llm_result = client.responses.create(
                    model=selected_model,
                    instructions="You are a safe, empathetic journaling and mental wellness support assistant.",
                    input=prompt,
                    temperature=0.7,
                    max_output_tokens=260,
                )
                parsed = _parse_llm_text(llm_result.output_text, emotion)
                parsed["source"] = f"OpenAI ({selected_model})"
                parsed["api_error"] = ""
                return parsed
            except Exception as responses_error:
                try:
                    llm_result = client.chat.completions.create(
                        model=selected_model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a safe, empathetic journaling and mental wellness support assistant.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.7,
                        max_tokens=260,
                    )
                    parsed = _parse_llm_text(llm_result.choices[0].message.content, emotion)
                    parsed["source"] = f"OpenAI ({selected_model}, chat)"
                    parsed["api_error"] = ""
                    return parsed
                except Exception as chat_error:
                    raise RuntimeError(
                        f"Responses API failed: {responses_error}; Chat Completions failed: {chat_error}"
                    ) from chat_error

        if provider == "OpenRouter":
            key = key or OPENROUTER_API_KEY.strip()
            if not key or key == "YOUR_API_KEY_HERE":
                raise ValueError("OpenRouter API key is missing.")

            from openai import OpenAI

            selected_model = model_name or OPENROUTER_MODEL
            client = OpenAI(
                base_url=OPENROUTER_BASE_URL,
                api_key=key,
                default_headers={
                    "HTTP-Referer": "http://localhost:8501",
                    "X-Title": "MindMitra AI",
                },
            )
            llm_result = client.chat.completions.create(
                model=selected_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a safe, empathetic journaling and mental wellness support assistant.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=260,
            )
            parsed = _parse_llm_text(llm_result.choices[0].message.content, emotion)
            parsed["source"] = f"OpenRouter ({selected_model})"
            parsed["api_error"] = ""
            return parsed

    except Exception as error:
        return _fallback_with_error(emotion, provider, error)

    return _fallback_response(emotion)

def save_entry(text, prediction, llm_response):
    """Save one journal entry with background ML analysis."""
    entries = load_entries()
    from datetime import datetime
    from zoneinfo import ZoneInfo
    created_at = datetime.now(ZoneInfo("UTC")).astimezone(ZoneInfo("Asia/Kolkata"))
    entry = {
        "timestamp": created_at.isoformat(timespec="seconds"),
        "date": created_at.strftime("%Y-%m-%d"),
        "time": created_at.strftime("%I:%M %p"),
        "display_date": created_at.strftime("%d %B %Y"),
        "weekday": created_at.strftime("%A"),
        "text": text.strip(),
        "emotion": prediction["emotion"],
        "sentiment": prediction["sentiment"],
        "emotion_confidence": round(prediction["emotion_confidence"], 4),
        "sentiment_confidence": round(prediction["sentiment_confidence"], 4),
        "ai_response": llm_response
    }
    

    entries.append(entry)
    with open("journal.json", "w") as f:
        json.dump(entries, f, indent=2)
    return entry
def load_entries():
    if not JOURNAL_PATH.exists():
        return []

    try:
        with open(JOURNAL_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        print("LOAD ERROR:", e)
        return []
def train_model():
    """Train TF-IDF + Logistic Regression models from local data plus samples."""
    local_df = load_local_dataset()
    sample_df = pd.DataFrame(SAMPLE_DATA, columns=["text", "sentiment", "emotion"])
    sample_df["source_file"] = "inline_samples"

    df = pd.concat([local_df, sample_df], ignore_index=True)
    df["clean_text"] = df["text"].apply(preprocess_text)
    df = df[df["clean_text"].str.len() > 0]

    sentiment_model = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=8000)),
            (
                "classifier",
                LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
            ),
        ]
    )

    emotion_model = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=8000)),
            (
                "classifier",
                LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
            ),
        ]
    )
    if df.empty:
        df = sample_df.copy()
    sentiment_model.fit(df["clean_text"], df["sentiment"])
    emotion_model.fit(df["clean_text"], df["emotion"])

    metadata = {
        "rows": len(df),
        "local_rows": len(local_df),
        "sources": sorted(local_df["source_file"].dropna().unique().tolist())
        if not local_df.empty
        else [],
    }

    return sentiment_model, emotion_model, metadata
class JournalRequest(BaseModel):
    text: str

class ChatRequest(BaseModel):
    messages: list[dict]
@app.post("/predict")
def predict(data: JournalRequest):
    prediction = predict_emotion(
        data.text,
        sentiment_model,
        emotion_model
    )
    return {"status": "success", "data": prediction}
@app.post("/save_entry")
def save(data: JournalRequest):
    print("Incoming text:", data.text)
    print("Saving to:", JOURNAL_PATH)

    prediction = predict_emotion(
        data.text,
        sentiment_model,
        emotion_model
    )
    print("Prediction:", prediction)

    llm_response = generate_llm_response(
        user_text=data.text,
        emotion=prediction["emotion"],
        sentiment=prediction["sentiment"],
        provider="OpenRouter"
    )
    print("LLM Response:", llm_response)

    entry = save_entry(data.text, prediction, llm_response)
    print("Saved Entry:", entry)
    support = MOOD_SUPPORT.get(prediction["emotion"], {})
    support = MOOD_SUPPORT.get(prediction["emotion"], {})
    return {
        "entry": entry,
        "support": support,
        "helplines": HELPLINES["India"]
    }
@app.get("/entries")
def get_entries():
    return {"status": "success", "data": load_entries()}
@app.post("/chat")
def chat(data: ChatRequest):
    response = generate_chat_response(
        messages=data.messages,
        provider="OpenRouter"
    )
    return response
def preprocess_text(text):
    """Clean text with lowercase and punctuation removal while keeping useful words."""
    text = str(text).lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
def _highest_probability(model, clean_text):
    probabilities = model.predict_proba([clean_text])[0]
    best_index = probabilities.argmax()
    label = model.classes_[best_index]
    confidence = float(probabilities[best_index])
    return label, confidence
def _build_prompt(user_text, emotion, sentiment):
    return f"""
You are MindMitra AI, a mental wellness journaling assistant.

The user has written a personal journal entry. Your job is to:
- Understand their emotions deeply
- Reflect their feelings so they feel heard
- Provide calm and supportive guidance
- Suggest small, practical steps

IMPORTANT:
- Do NOT ask any questions
- Do NOT act like a chatbot
- Do NOT continue a conversation
- Keep it reflective and supportive
- Keep tone calm, warm, and validating

User Journal:
"{user_text}"

Emotion: {emotion}
Sentiment: {sentiment}

Respond in this JSON format:
{{
  "supportive_response": "A validating response that reflects their feelings",
  "insight": "A gentle psychological insight about their situation",
  "suggestion": "1–2 small practical steps",
  "motivation": "A short reassuring statement",
  "reply": "A well-written paragraph combining all above"
}}
"""
def _parse_llm_text(text, emotion):
    try:
        # Extract JSON from text (in case extra text exists)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        json_str = match.group() if match else text

        parsed = json.loads(json_str)

        return {
            "supportive_response": parsed.get("supportive_response", ""),
            "insight": parsed.get("insight", ""),
            "suggestion": parsed.get("suggestion", ""),
            "motivation": parsed.get("motivation", ""),
            "reply": parsed.get("reply", "")
        }

    except Exception as e:
        # fallback if parsing fails
        return {
            "supportive_response": text,
            "insight": "",
            "suggestion": "",
            "motivation": "",
            "reply": text
        }
def _fallback_response(emotion, source_note="Rule-based fallback"):
    response = FALLBACK_RESPONSES.get(emotion, FALLBACK_RESPONSES["Sad"]).copy()
    response["reply"] = (
        f"{response['supportive_response']} {response['suggestion']} "
        f"{response['motivation']} What feels like the smallest kind thing you could do for yourself right now?"
    )
    response["source"] = source_note
    response["api_error"] = ""
    return response
def _fallback_with_error(emotion, provider, error):
    response = _fallback_response(
        emotion,
        source_note=f"{provider} unavailable. Showing rule-based fallback.",
    )
    response["api_error"] = f"{type(error).__name__}: {str(error)}"
    return response
def load_local_dataset():
    """Load CSV, TXT, or ZIP datasets from the app folder."""
    frames = []
    candidates = []

    for pattern in ("*.csv", "*.txt", "*.zip"):
        candidates.extend(PROJECT_DIR.glob(pattern))

    for path in candidates:
        if path.name.lower() in {"requirements.txt", "journal.json"}:
            continue

        try:
            if path.suffix.lower() == ".csv":
                frame = parse_csv_dataset(path)
            elif path.suffix.lower() == ".txt":
                frame = parse_txt_dataset(path)
            elif path.suffix.lower() == ".zip":
                frame = parse_zip_dataset(path)
            else:
                continue

            if not frame.empty:
                frame["source_file"] = path.name
                frames.append(frame)
        except Exception:
            continue

    if not frames:
        return pd.DataFrame(columns=["text", "emotion", "sentiment", "source_file"])

    dataset = pd.concat(frames, ignore_index=True)
    dataset = dataset.dropna(subset=["text", "emotion", "sentiment"])
    dataset = dataset[dataset["emotion"].isin(SUPPORTED_EMOTIONS)]
    dataset = dataset[dataset["sentiment"].isin(SUPPORTED_SENTIMENTS)]
    dataset = dataset.drop_duplicates(subset=["text"])
    return dataset
def _entry_datetime(entry):
    try:
        if "timestamp" in entry:
            return datetime.fromisoformat(entry["timestamp"])
    except:
        pass
    return datetime.now()
def _normalize_journal_entry(entry):
    """Keep older saved entries compatible with the date-wise journal view."""
    entry = dict(entry)
    created_at = _entry_datetime(entry)
    entry["timestamp"] = created_at.isoformat(timespec="seconds")
    entry["date"] = entry.get("date") or created_at.strftime("%Y-%m-%d")
    entry["time"] = entry.get("time") or created_at.strftime("%I:%M %p")
    entry["display_date"] = entry.get("display_date") or created_at.strftime("%d %B %Y")
    entry["weekday"] = entry.get("weekday") or created_at.strftime("%A")
    entry["text"] = entry.get("text", "")
    entry["emotion"] = entry.get("emotion", "Sad")
    entry["sentiment"] = entry.get("sentiment", "Negative")
    entry["emotion_confidence"] = float(entry.get("emotion_confidence", 0))
    entry["sentiment_confidence"] = float(entry.get("sentiment_confidence", 0))
    entry["ai_response"] = entry.get("ai_response") or _fallback_response(entry["emotion"])
    if "reply" not in entry["ai_response"]:
        old_response = entry["ai_response"]
        entry["ai_response"]["reply"] = " ".join(
            part
            for part in [
                old_response.get("supportive_response", ""),
                old_response.get("suggestion", ""),
                old_response.get("motivation", ""),
            ]
            if part
        ).strip()
    return entry
def generate_chat_response(messages, provider="OpenRouter", api_key=None, model_name=None):
    """Generate a conversational follow-up response after journaling."""
    if provider == "Fallback only":
        return {
            "role": "assistant",
            "content": (
                "I'm here with you. It may help to name the main feeling in one sentence, "
                "then choose one small next step. What part of this feels heaviest right now?"
            ),
            "source": "Rule-based fallback",
            "api_error": "",
        }

    key = (api_key or "").strip()
    system_message = {
        "role": "system",
        "content": (
            "You are MindMitra AI, a safe and empathetic journaling companion. "
            "Reply conversationally, validate feelings, ask gentle follow-up questions, "
            "and offer practical non-medical coping steps. Do not diagnose or claim to replace therapy. "
            "If the user may be unsafe, encourage immediate support from local emergency services or a trusted person."
        ),
    }

    try:
        if provider == "OpenRouter":
            key = key or OPENROUTER_API_KEY.strip()
            if not key or key == "YOUR_API_KEY_HERE":
                raise ValueError("OpenRouter API key is missing.")

            from openai import OpenAI

            client = OpenAI(
                base_url=OPENROUTER_BASE_URL,
                api_key=key,
                default_headers={
                    "HTTP-Referer": "http://localhost:8501",
                    "X-Title": "MindMitra AI",
                },
            )
            selected_model = model_name or OPENROUTER_MODEL
            result = client.chat.completions.create(
                model=selected_model,
                messages=[system_message] + messages[-8:],
                temperature=0.75,
                max_tokens=300,
            )
            return {
                "role": "assistant",
                "content": result.choices[0].message.content,
                "source": f"OpenRouter ({selected_model})",
                "api_error": "",
            }

        if provider == "OpenAI":
            key = key or OPENAI_API_KEY.strip()
            if not key or key == "YOUR_API_KEY_HERE":
                raise ValueError("OpenAI API key is missing.")

            from openai import OpenAI

            selected_model = model_name or OPENAI_MODEL
            client = OpenAI(api_key=key)
            result = client.chat.completions.create(
                model=selected_model,
                messages=[system_message] + messages[-8:],
                temperature=0.75,
                max_tokens=300,
            )
            return {
                "role": "assistant",
                "content": result.choices[0].message.content,
                "source": f"OpenAI ({selected_model})",
                "api_error": "",
            }

        if provider == "Google Gemini":
            key = key or GEMINI_API_KEY.strip()
            if not key or key == "YOUR_API_KEY_HERE":
                raise ValueError("Gemini API key is missing.")

            import google.generativeai as genai

            transcript = "\n".join(
                f"{message['role']}: {message['content']}" for message in messages[-8:]
            )
            genai.configure(api_key=key)
            model = genai.GenerativeModel(GEMINI_MODEL)
            result = model.generate_content(system_message["content"] + "\n\nConversation:\n" + transcript)
            return {
                "role": "assistant",
                "content": result.text,
                "source": f"Google Gemini ({GEMINI_MODEL})",
                "api_error": "",
            }

    except Exception as error:
        return {
            "role": "assistant",
            "content": (
                "I couldn't reach the AI service just now, but I'm still here. "
                "Try taking one slow breath and telling me what feeling is most present for you."
            ),
            "source": f"{provider} unavailable. Showing rule-based fallback.",
            "api_error": f"{type(error).__name__}: {str(error)}",
        }

    return {
        "role": "assistant",
        "content": "I'm here with you. What would you like to talk through next?",
        "source": "Rule-based fallback",
        "api_error": "",
    }
def parse_csv_dataset(path):
    try:
        df = pd.read_csv(path)
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="latin-1")

    text_col = detect_text_column(df)
    emotion_col, sentiment_col = detect_label_columns(df)
    if not text_col or not (emotion_col or sentiment_col):
        return pd.DataFrame(columns=["text", "emotion", "sentiment"])

    rows = []
    for _, row in df.iterrows():
        item = normalize_training_row(
            text=row[text_col],
            emotion=row[emotion_col] if emotion_col else None,
            sentiment=row[sentiment_col] if sentiment_col else None,
        )
        if item:
            rows.append(item)

    return pd.DataFrame(rows)

def parse_txt_dataset(path):
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    return parse_txt_lines(lines)


def parse_zip_dataset(path):
    frames = []

    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            suffix = Path(name).suffix.lower()
            if suffix == ".txt":
                with archive.open(name) as file:
                    lines = file.read().decode("utf-8", errors="ignore").splitlines()
                frames.append(parse_txt_lines(lines))
            elif suffix == ".csv":
                with archive.open(name) as file:
                    try:
                        df = pd.read_csv(file)
                    except UnicodeDecodeError:
                        file.seek(0)
                        df = pd.read_csv(file, encoding="latin-1")

                text_col = detect_text_column(df)
                emotion_col, sentiment_col = detect_label_columns(df)
                if text_col and (emotion_col or sentiment_col):
                    rows = []
                    for _, row in df.iterrows():
                        item = normalize_training_row(
                            text=row[text_col],
                            emotion=row[emotion_col] if emotion_col else None,
                            sentiment=row[sentiment_col] if sentiment_col else None,
                        )
                        if item:
                            rows.append(item)
                    frames.append(pd.DataFrame(rows))

    if frames:
        return pd.concat(frames, ignore_index=True)
    return pd.DataFrame(columns=["text", "emotion", "sentiment"])
sentiment_model, emotion_model, metadata = train_model()





