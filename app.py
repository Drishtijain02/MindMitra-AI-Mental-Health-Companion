import os
import re
import json
import time
import base64
import zipfile
from html import escape
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_API_KEY_HERE")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "YOUR_API_KEY_HERE")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
PROJECT_DIR = Path(__file__).resolve().parent
JOURNAL_PATH = PROJECT_DIR / "journal.json"

SUPPORTED_EMOTIONS = ["Happy", "Sad", "Stress", "Anxiety"]
SUPPORTED_SENTIMENTS = ["Positive", "Neutral", "Negative"]

SENTIMENT_BY_EMOTION = {
    "Happy": "Positive",
    "Sad": "Negative",
    "Stress": "Negative",
    "Anxiety": "Negative",
}

MOOD_SCORE = {
    "Sad": 1,
    "Anxiety": 2,
    "Stress": 2,
    "Happy": 4,
}

# The included Kaggle TXT file uses one-hot labels.
# Common order: joy, fear, anger, sadness, disgust, shame, guilt.
ONE_HOT_EMOTION_MAP = {
    0: "Happy",
    1: "Anxiety",
    2: "Stress",
    3: "Sad",
    4: "Stress",
    5: "Anxiety",
    6: "Sad",
}


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "has",
    "have",
    "i",
    "in",
    "is",
    "it",
    "its",
    "me",
    "my",
    "of",
    "on",
    "or",
    "our",
    "so",
    "that",
    "the",
    "this",
    "to",
    "was",
    "we",
    "were",
    "with",
    "you",
    "your",
}


SAMPLE_DATA = [
    ("I feel calm and grateful today. My morning was peaceful.", "Positive", "Happy"),
    ("I am proud of myself because I finished my work on time.", "Positive", "Happy"),
    ("I laughed with my friends and felt hopeful about the future.", "Positive", "Happy"),
    ("Today felt bright, balanced, and full of good energy.", "Positive", "Happy"),
    ("I feel excited about the progress I am making.", "Positive", "Happy"),
    ("I had a warm conversation and it lifted my mood.", "Positive", "Happy"),
    ("I feel thankful for small things and I am smiling more.", "Positive", "Happy"),
    ("I am feeling confident, refreshed, and motivated.", "Positive", "Happy"),
    ("I feel lonely and heavy. Nothing seems enjoyable right now.", "Negative", "Sad"),
    ("I cried today because I miss someone very much.", "Negative", "Sad"),
    ("Everything feels dull and I do not have energy.", "Negative", "Sad"),
    ("I feel disappointed, tired, and emotionally low.", "Negative", "Sad"),
    ("I feel empty and disconnected from the people around me.", "Negative", "Sad"),
    ("I keep thinking about my mistakes and it makes me sad.", "Negative", "Sad"),
    ("I do not feel like talking to anyone today.", "Negative", "Sad"),
    ("My heart feels heavy and I need comfort.", "Negative", "Sad"),
    ("I have too many deadlines and I cannot relax.", "Negative", "Stress"),
    ("Work is piling up and I feel pressured all day.", "Negative", "Stress"),
    ("I am exhausted because there is too much responsibility.", "Negative", "Stress"),
    ("My schedule is packed and I feel burned out.", "Negative", "Stress"),
    ("I am under pressure and my mind feels overloaded.", "Negative", "Stress"),
    ("I need a break because everything feels urgent.", "Negative", "Stress"),
    ("I feel frustrated by tasks, meetings, and expectations.", "Negative", "Stress"),
    ("There is so much to handle that I feel tense.", "Negative", "Stress"),
    ("I keep worrying that something bad will happen.", "Negative", "Anxiety"),
    ("My chest feels tight and my thoughts are racing.", "Negative", "Anxiety"),
    ("I am nervous about tomorrow and cannot stop overthinking.", "Negative", "Anxiety"),
    ("I feel scared, restless, and uncertain about everything.", "Negative", "Anxiety"),
    ("I am anxious about an upcoming exam and cannot sleep.", "Negative", "Anxiety"),
    ("My mind is full of what if questions.", "Negative", "Anxiety"),
    ("I feel panic rising when I think about the future.", "Negative", "Anxiety"),
    ("I am worried people will judge me.", "Negative", "Anxiety"),
    ("Today was ordinary. I completed a few tasks and rested.", "Neutral", "Happy"),
    ("Nothing special happened, but I feel steady.", "Neutral", "Happy"),
    ("I am okay today, neither very happy nor very upset.", "Neutral", "Happy"),
    ("The day was normal and manageable.", "Neutral", "Happy"),
    ("I feel a little tired but mostly stable.", "Neutral", "Stress"),
    ("I had some work, but it was not overwhelming.", "Neutral", "Stress"),
    ("I am thinking about plans, but I feel mostly fine.", "Neutral", "Anxiety"),
    ("I had quiet moments and some worries, but I handled them.", "Neutral", "Anxiety"),
    ("today was kinda rough day", "Negative", "Stress"),
]


EMOTION_STYLE = {
    "Happy": {
        "label": "Positive",
        "color": "#16a34a",
        "background": "#ecfdf5",
        "border": "#86efac",
        "streamlit_state": "success",
    },
    "Sad": {
        "label": "Low",
        "color": "#2563eb",
        "background": "#eff6ff",
        "border": "#93c5fd",
        "streamlit_state": "warning",
    },
    "Stress": {
        "label": "Tense",
        "color": "#ca8a04",
        "background": "#fffbeb",
        "border": "#fde68a",
        "streamlit_state": "warning",
    },
    "Anxiety": {
        "label": "Worried",
        "color": "#dc2626",
        "background": "#fef2f2",
        "border": "#fca5a5",
        "streamlit_state": "error",
    },
}

FALLBACK_RESPONSES = {
    "Happy": {
        "supportive_response": (
            "It is wonderful that you are noticing positive energy today. Let yourself fully enjoy this moment."
        ),
        "suggestion": "Write down one thing that helped you feel this way so you can return to it later.",
        "motivation": "Small joyful moments are real progress too.",
    },
    "Sad": {
        "supportive_response": (
            "I am sorry you are feeling low. Your emotions are valid, and you do not have to handle them all at once."
        ),
        "suggestion": "Try one gentle action: drink water, step outside for two minutes, or message someone you trust.",
        "motivation": "A hard day does not define your whole story.",
    },
    "Stress": {
        "supportive_response": (
            "It sounds like you are carrying a lot. Feeling stretched under pressure is understandable."
        ),
        "suggestion": "Choose one small task, set a 10-minute timer, and pause before deciding what comes next.",
        "motivation": "You can move through this one manageable step at a time.",
    },
    "Anxiety": {
        "supportive_response": (
            "Anxious thoughts can feel very loud. You are safe to slow down and come back to the present moment."
        ),
        "suggestion": "Try the 5-4-3-2-1 grounding exercise: name 5 things you see, 4 you feel, 3 you hear, 2 you smell, and 1 you taste.",
        "motivation": "This feeling can pass, and you can meet it with patience.",
    },
}

MOOD_MUSIC_QUERIES = {
    "Happy": "feel good uplifting pop",
    "Sad": "soft acoustic comfort songs",
    "Stress": "calm relaxing instrumental focus",
    "Anxiety": "peaceful piano calming meditation",
}


def preprocess_text(text):
    """Clean text with lowercase and punctuation removal while keeping useful words."""
    text = str(text).lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_emotion(label):
    """Map common dataset labels into the app's four emotion classes."""
    label = str(label).strip().lower()

    if label in {"happy", "happiness", "joy", "love", "positive", "relief"}:
        return "Happy"
    if label in {"sad", "sadness", "grief", "depression", "depressed", "lonely", "guilt", "guilty"}:
        return "Sad"
    if label in {"stress", "stressed", "anger", "angry", "frustration", "disgust", "tension"}:
        return "Stress"
    if label in {"anxiety", "anxious", "fear", "worry", "worried", "nervous", "shame"}:
        return "Anxiety"

    return None


def normalize_sentiment(label):
    """Map sentiment labels into Positive, Neutral, or Negative."""
    label = str(label).strip().lower()

    if label in {"positive", "pos", "happy", "joy", "love", "relief"}:
        return "Positive"
    if label in {"neutral", "normal", "mixed"}:
        return "Neutral"
    if label in {
        "negative",
        "neg",
        "sad",
        "sadness",
        "stress",
        "stressed",
        "anxiety",
        "anxious",
        "fear",
        "anger",
        "disgust",
        "shame",
        "guilt",
    }:
        return "Negative"

    return None


def detect_text_column(df):
    preferred = ["text", "content", "sentence", "message", "journal", "entry", "tweet", "statement"]
    lowered_columns = {column.lower().strip(): column for column in df.columns}

    for name in preferred:
        if name in lowered_columns:
            return lowered_columns[name]

    text_like_columns = [
        column for column in df.columns if df[column].astype(str).str.len().mean() > 20
    ]
    return text_like_columns[0] if text_like_columns else None


def detect_label_columns(df):
    lowered_columns = {column.lower().strip(): column for column in df.columns}
    emotion_col = None
    sentiment_col = None

    for name in ["emotion", "label", "category", "class"]:
        if name in lowered_columns:
            emotion_col = lowered_columns[name]
            break

    for name in ["sentiment", "polarity", "sentiment_label"]:
        if name in lowered_columns:
            sentiment_col = lowered_columns[name]
            break

    return emotion_col, sentiment_col


def normalize_training_row(text, emotion=None, sentiment=None):
    text = str(text).strip()
    if not text or text.lower() == "nan":
        return None

    emotion = normalize_emotion(emotion) if emotion is not None else None
    sentiment = normalize_sentiment(sentiment) if sentiment is not None else None

    if not emotion and sentiment == "Positive":
        emotion = "Happy"
    elif not emotion and sentiment == "Negative":
        emotion = "Sad"

    if emotion and not sentiment:
        sentiment = SENTIMENT_BY_EMOTION.get(emotion, "Neutral")

    if emotion in SUPPORTED_EMOTIONS and sentiment in SUPPORTED_SENTIMENTS:
        return {"text": text, "emotion": emotion, "sentiment": sentiment}

    return None


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


def parse_txt_lines(lines):
    rows = []
    one_hot_pattern = re.compile(r"^\s*\[(.*?)\]\s*(.+)$")

    for line in lines:
        line = str(line).strip()
        if not line:
            continue

        match = one_hot_pattern.match(line)
        if match:
            raw_numbers, text = match.groups()
            numbers = [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", raw_numbers)]
            if numbers:
                index = max(range(len(numbers)), key=numbers.__getitem__)
                emotion = ONE_HOT_EMOTION_MAP.get(index)
                item = normalize_training_row(
                    text=text,
                    emotion=emotion,
                    sentiment=SENTIMENT_BY_EMOTION.get(emotion, "Neutral"),
                )
                if item:
                    rows.append(item)
            continue

        for separator in ["\t", ";", ","]:
            if separator not in line:
                continue

            left, right = [part.strip() for part in line.split(separator, 1)]
            item = normalize_training_row(text=right, emotion=left, sentiment=left)
            if not item:
                item = normalize_training_row(text=left, emotion=right, sentiment=right)
            if item:
                rows.append(item)
                break

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


@st.cache_resource
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


def _highest_probability(model, clean_text):
    probabilities = model.predict_proba([clean_text])[0]
    best_index = probabilities.argmax()
    label = model.classes_[best_index]
    confidence = float(probabilities[best_index])
    return label, confidence


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


def _build_prompt(user_text, emotion, sentiment):
    return f"""
You are MindMitra AI, a warm, emotionally aware journaling companion.
The user wrote this journal entry:
\"\"\"{user_text}\"\"\"

Detected sentiment: {sentiment}
Detected emotion: {emotion}

Write one natural, conversational response like a caring chat assistant.
Make it detailed enough to feel helpful, but not too long.
Reflect what the user may be feeling, gently validate them, and offer practical next steps in a friendly tone.
Ask one thoughtful follow-up question at the end so the user can continue the conversation.

Do not diagnose. Do not claim to replace therapy.
If the user may be in danger, gently encourage immediate support from a trusted person or local emergency services.
"""


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


def _parse_llm_text(text, emotion):
    fallback = _fallback_response(emotion)
    if not text or str(text).strip().lower() in ["none", ""]:
        return fallback
    text = str(text).strip()
    if text:
        return {
            "reply": text,
            "supportive_response": text,
            "suggestion": "",
            "motivation": "",
        }

    parsed = {
        "reply": fallback["reply"],
        "supportive_response": fallback["supportive_response"],
        "suggestion": fallback["suggestion"],
        "motivation": fallback["motivation"],
    }

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        cleaned_line = line.strip("*- ")
        normalized = cleaned_line.lower()
        if normalized.startswith("supportive response:") or normalized.startswith("supportive message:"):
            parsed["supportive_response"] = cleaned_line.split(":", 1)[1].strip()
        elif normalized.startswith("wellness suggestion:") or normalized.startswith("suggestion:"):
            parsed["suggestion"] = cleaned_line.split(":", 1)[1].strip()
        elif normalized.startswith("motivational message:") or normalized.startswith("motivation:"):
            parsed["motivation"] = cleaned_line.split(":", 1)[1].strip()

    parsed["reply"] = " ".join(
        part
        for part in [parsed["supportive_response"], parsed["suggestion"], parsed["motivation"]]
        if part
    ).strip()
    return parsed


def generate_llm_response(user_text, emotion, sentiment, provider="Fallback only", api_key=None, model_name=None):
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


def generate_chat_response(messages, provider="Fallback only", api_key=None, model_name=None):
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


def get_secret_value(name, default=""):
    """Read keys from environment variables or Streamlit secrets without crashing locally."""
    if os.getenv(name):
        return os.getenv(name)
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def get_spotify_access_token(client_id, client_secret):
    """Use Spotify Client Credentials flow for public catalog search."""
    client_id = (client_id or get_secret_value("SPOTIFY_CLIENT_ID", SPOTIFY_CLIENT_ID)).strip()
    client_secret = (client_secret or get_secret_value("SPOTIFY_CLIENT_SECRET", SPOTIFY_CLIENT_SECRET)).strip()

    if not client_id or not client_secret:
        return None, "Spotify Client ID and Client Secret are required."

    cached_token = st.session_state.get("spotify_access_token")
    token_expires_at = st.session_state.get("spotify_token_expires_at", 0)
    if cached_token and time.time() < token_expires_at - 60:
        return cached_token, ""

    credentials = f"{client_id}:{client_secret}".encode("utf-8")
    encoded_credentials = base64.b64encode(credentials).decode("utf-8")
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    response = requests.post(
        SPOTIFY_TOKEN_URL,
        headers=headers,
        data={"grant_type": "client_credentials"},
        timeout=15,
    )

    if response.status_code != 200:
        try:
            detail = response.json().get("error_description") or response.json().get("error")
        except Exception:
            detail = response.text
        return None, f"Spotify token request failed ({response.status_code}): {detail}"

    data = response.json()
    access_token = data.get("access_token")
    expires_in = int(data.get("expires_in", 3600))
    st.session_state["spotify_access_token"] = access_token
    st.session_state["spotify_token_expires_at"] = time.time() + expires_in
    return access_token, ""


def spotify_get(path, access_token, params=None, max_retries=2):
    """Call Spotify Web API and respect Retry-After on rate limits."""
    url = f"{SPOTIFY_API_BASE_URL}{path}"
    headers = {"Authorization": f"Bearer {access_token}"}

    for attempt in range(max_retries + 1):
        response = requests.get(url, headers=headers, params=params or {}, timeout=15)
        if response.status_code == 429 and attempt < max_retries:
            retry_after = int(response.headers.get("Retry-After", "1"))
            time.sleep(min(retry_after, 8))
            continue

        if response.status_code >= 400:
            try:
                error_data = response.json().get("error", {})
                message = error_data.get("message") or response.text
            except Exception:
                message = response.text
            return None, f"Spotify API error ({response.status_code}): {message}"

        return response.json(), ""

    return None, "Spotify rate limit reached. Please try again in a moment."


def search_spotify_tracks(emotion, client_id="", client_secret="", market="IN", limit=3):
    """Search public Spotify catalog tracks for a mood. Results are not cached."""
    access_token, token_error = get_spotify_access_token(client_id, client_secret)
    if token_error:
        return [], token_error

    query = MOOD_MUSIC_QUERIES.get(emotion, "calm relaxing songs")
    data, api_error = spotify_get(
        "/search",
        access_token,
        params={
            "q": query,
            "type": "track",
            "market": market,
            "limit": limit,
        },
    )
    if api_error:
        return [], api_error

    tracks = []
    for item in data.get("tracks", {}).get("items", []):
        album_images = item.get("album", {}).get("images", [])
        tracks.append(
            {
                "name": item.get("name", "Unknown track"),
                "artists": ", ".join(artist.get("name", "Unknown artist") for artist in item.get("artists", [])),
                "url": item.get("external_urls", {}).get("spotify", ""),
                "image": album_images[0]["url"] if album_images else "",
                "query": query,
            }
        )

    return tracks, ""


def render_youtube_music(emotion):
    st.subheader("🎧 Music for your mood")

    MOOD_QUERIES = {
        "Happy": "happy upbeat music playlist",
        "Sad": "sad emotional songs playlist",
        "Stress": "relaxing instrumental music",
        "Anxiety": "calm meditation music"
    }

    MOOD_VIDEOS = {
        "Happy": "https://www.youtube.com/watch?v=ZbZSe6N_BXs",
        "Sad": "https://www.youtube.com/watch?v=2Vv-BfVoq4g",
        "Stress": "https://www.youtube.com/watch?v=5qap5aO4i9A",
        "Anxiety": "https://www.youtube.com/watch?v=1ZYbU82GVz4"
    }

    query = MOOD_QUERIES.get(emotion, "relaxing music")
    video_url = MOOD_VIDEOS.get(emotion)

    st.markdown("##### Suggested for you 💙")

    # Show embedded video (premium feel)
    if video_url:
        st.video(video_url)

    # Backup: YouTube search link
    search_url = f"https://www.youtube.com/results?search_query={query}"
    st.link_button("🔎 Explore more on YouTube", search_url)

def render_emotion_card(emotion, sentiment, emotion_confidence, sentiment_confidence):
    style = EMOTION_STYLE[emotion]
    st.markdown(
        f"""
        <div class="emotion-card" style="background:{style['background']}; border-color:{style['border']};">
            <div class="emotion-topline" style="color:{style['color']};">
                <span class="emotion-emoji">{escape(emotion)}</span>
            </div>
            <div class="metric-grid">
                <div>
                    <p class="metric-label">Sentiment</p>
                    <p class="metric-value">{escape(sentiment)}</p>
                </div>
                <div>
                    <p class="metric-label">Emotion Confidence</p>
                    <p class="metric-value">{emotion_confidence:.1%}</p>
                </div>
                <div>
                    <p class="metric-label">Sentiment Confidence</p>
                    <p class="metric-value">{sentiment_confidence:.1%}</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _entry_datetime(entry):
    timestamp = entry.get("timestamp") or f"{entry.get('date', '')} {entry.get('time', '')}".strip()
    parsed = pd.to_datetime(timestamp, errors="coerce")
    if pd.isna(parsed):
        parsed = pd.Timestamp.now()
    return parsed.to_pydatetime()


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


def load_entries():
    """Load saved journal entries from local JSON storage."""
    if not JOURNAL_PATH.exists():
        return []

    try:
        data = json.loads(JOURNAL_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return []
        return [_normalize_journal_entry(entry) for entry in data]
    except (json.JSONDecodeError, OSError):
        return []


def save_entry(text, prediction, llm_response):
    """Save one journal entry with background ML analysis."""
    entries = load_entries()
    created_at = datetime.now()
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
        "ai_response": llm_response,
    }
    entries.append(entry)
    JOURNAL_PATH.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    return entry


def entries_to_dataframe(entries):
    if not entries:
        return pd.DataFrame()

    df = pd.DataFrame(entries)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])
    df["date"] = df["timestamp"].dt.date
    df["mood_score"] = df["emotion"].map(MOOD_SCORE).fillna(2)
    return df.sort_values("timestamp")


def generate_insights(entries):
    """Create simple wellness insights from saved journal entries."""
    df = entries_to_dataframe(entries)
    if df.empty:
        return ["Start journaling to unlock personal mood insights."]

    insights = []
    recent = df.tail(5)
    top_emotion = recent["emotion"].mode().iloc[0]

    if top_emotion == "Stress":
        insights.append("You have been feeling stressed frequently in recent entries.")
    elif top_emotion == "Anxiety":
        insights.append("Anxiety has appeared often lately. Grounding routines may help.")
    elif top_emotion == "Sad":
        insights.append("Your recent entries show a lower emotional tone. Gentle support may be useful.")
    elif top_emotion == "Happy":
        insights.append("Positive emotions are showing up often in your recent journal entries.")

    if len(df) >= 4:
        older_avg = df.iloc[:-2]["mood_score"].tail(5).mean()
        recent_avg = df.tail(2)["mood_score"].mean()
        if recent_avg > older_avg:
            insights.append("Your mood appears to be improving compared with earlier entries.")
        elif recent_avg < older_avg:
            insights.append("Your mood has dipped recently, so this may be a good time to slow down.")

    if recent["emotion"].isin(["Stress", "Anxiety"]).sum() >= 3:
        insights.append("Stress or anxiety appears in most recent entries. Consider adding a short daily reset.")

    if len(insights) == 1 and len(df) < 4:
        insights.append("Keep writing for a few more days to build stronger trend insights.")

    return insights[:3]


def render_ai_response(llm_response, show_diagnostics=False):
    reply = llm_response.get("reply")
    if not reply:
        reply = " ".join(
            part
            for part in [
                llm_response.get("supportive_response", ""),
                llm_response.get("suggestion", ""),
                llm_response.get("motivation", ""),
            ]
            if part
        ).strip()

    st.markdown(
        f"""
        <div class="response-box">
            <h4>MindMitra</h4>
            <p>{escape(reply)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"Response source: {llm_response['source']}")
    if show_diagnostics and llm_response.get("api_error"):
        st.error(f"API diagnostic: {llm_response['api_error']}")



def render_chat_companion(provider, api_key, selected_model, show_diagnostics=False):
    st.subheader("Talk With MindMitra")
    st.caption("This chat is for support after journaling. It is not saved as a journal entry.")

    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []

    if not st.session_state["chat_messages"] and "last_saved_entry" in st.session_state:
        latest = st.session_state["last_saved_entry"]
        st.session_state["chat_messages"].append(
            {
                "role": "assistant",
                "content": (
                    "I read your journal entry. We can sit with it together. "
                    f"It sounded mostly like {latest['emotion'].lower()} with {latest['sentiment'].lower()} sentiment. "
                    "What part would you like to talk about first?"
                ),
            }
        )

    chat_box = st.container(height=260)
    with chat_box:
        for message in st.session_state["chat_messages"]:
            with st.chat_message(message["role"]):
                st.write(message["content"])

    with st.form("mindmitra_chat_form", clear_on_submit=True):
        chat_input = st.text_area(
            "Continue the conversation",
            height=90,
            placeholder="Tell MindMitra what you want to talk through...",
        )
        send_chat = st.form_submit_button("Send", use_container_width=True)

    if send_chat and chat_input.strip():
        st.session_state["chat_messages"].append({"role": "user", "content": chat_input.strip()})
        response = generate_chat_response(
            messages=st.session_state["chat_messages"],
            provider=provider,
            api_key=api_key,
            model_name=selected_model,
        )
        st.session_state["chat_messages"].append(
            {"role": "assistant", "content": response["content"]}
        )
        st.session_state["last_chat_source"] = response["source"]
        st.session_state["last_chat_error"] = response.get("api_error", "")
        st.rerun()

    if st.session_state.get("last_chat_source"):
        st.caption(f"Chat response source: {st.session_state['last_chat_source']}")
    if show_diagnostics and st.session_state.get("last_chat_error"):
        st.error(f"Chat API diagnostic: {st.session_state['last_chat_error']}")


def render_journal_archive(entries, show_diagnostics=False):
    if not entries:
        st.info("Your dated journal archive will appear here after your first saved entry.")
        return

    st.subheader("Journal Archive")
    df = entries_to_dataframe(entries)
    date_options = ["All dates"] + [
        date.strftime("%d %B %Y") for date in sorted(df["timestamp"].dt.date.unique(), reverse=True)
    ]
    selected_date = st.selectbox("View entries", date_options)

    visible_entries = list(reversed(entries))
    if selected_date != "All dates":
        visible_entries = [
            entry for entry in visible_entries if entry.get("display_date") == selected_date
        ]

    for entry in visible_entries:
        style = EMOTION_STYLE.get(entry["emotion"], EMOTION_STYLE["Sad"])
        title = (
            f"{entry.get('display_date', entry.get('date', 'Saved entry'))} - "
            f"{entry.get('time', '')} - {entry['emotion']}"
        )
        with st.expander(title, expanded=False):
            st.markdown(
                f"""
                <div class="journal-entry" style="border-left-color:{style['color']};">
                    <p class="journal-meta">{escape(entry.get('weekday', ''))} - {escape(entry.get('sentiment', ''))} sentiment - {float(entry.get('emotion_confidence', 0)):.1%} confidence</p>
                    <p class="journal-text">{escape(entry.get('text', ''))}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("**MindMitra Response**")
            render_ai_response(entry.get("ai_response") or _fallback_response(entry["emotion"]), show_diagnostics)
            render_youtube_music(entry["emotion"])


def render_charts(entries):
    df = entries_to_dataframe(entries)
    if df.empty:
        st.info("Charts will appear after you save entries.")
        return

    st.subheader("Emotion Frequency")
    mood_counts = df["emotion"].value_counts().reindex(SUPPORTED_EMOTIONS, fill_value=0)
    st.bar_chart(mood_counts)

    st.subheader("Emotional Trend")
    trend_df = df[["timestamp", "mood_score"]].set_index("timestamp")
    st.line_chart(trend_df)
    st.caption("Mood score: Sad=1, Anxiety/Stress=2, Happy=4")


def apply_page_styles():
    st.markdown("""
    <style>

/* MAIN BACKGROUND */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
}

/* SIDEBAR */
[data-testid="stSidebar"] {
    background: #0f172a;
}
[data-testid="stSidebar"] * {
    color: #f8fafc;
}

/* HEADINGS */
h1, h2, h3 {
    color: #0f172a !important;
}

/* TEXT VISIBILITY FIX */
p, span, label {
    color: #1e293b !important;
}

/* HERO SECTION */
.hero {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 8px 25px rgba(0,0,0,0.06);
}

/* SECTION BOX */
.section-shell {
    background: #ffffff;
    border-radius: 12px;
    padding: 1.2rem;
    border: 1px solid #e2e8f0;
    box-shadow: 0 6px 20px rgba(0,0,0,0.05);
}

/* INPUT BOX */
textarea {
    background: #f8fafc !important;
    color: #0f172a !important;
    border-radius: 10px !important;
}

/* BUTTON */
.stButton>button {
    background: #2563eb;
    color: white;
    border-radius: 10px;
    font-weight: 600;
}
.stButton>button:hover {
    background: #1d4ed8;
}

/* RESPONSE BOX */
.response-box {
    background: #f0fdf4;
    border: 1px solid #86efac;
    color: #14532d;
    border-radius: 10px;
}

/* JOURNAL ENTRY */
.journal-entry {
    background: #ffffff;
    border-left: 4px solid #2563eb;
    border-radius: 8px;
}

/* FIX LIGHT TEXT */
.metric-label {
    color: #475569 !important;
}
.metric-value {
    color: #020617 !important;
}

/* CHART AREA */
canvas {
    background: #ffffff !important;
    border-radius: 10px;
}

/* SPOTIFY CARD */
.spotify-track {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
}

/* CLEAN SPACING */
.block-container {
    padding-top: 2rem;
}

</style>
""", unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_title="MindMitra AI",
        page_icon="M",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_page_styles()

    sentiment_model, emotion_model, model_metadata = train_model()
    entries = load_entries()

    with st.sidebar:
        st.header("MindMitra AI")
        st.write("An AI-powered journaling assistant with mood tracking and supportive responses.")
        st.divider()
        provider = st.selectbox(
            "AI response engine",
            ["OpenRouter", "Google Gemini", "OpenAI", "Fallback only"],
            help="Fallback mode works without any API key.",
        )
        api_key = ""
        selected_model = OPENROUTER_MODEL
        if provider != "Fallback only":
            api_key = st.text_input(
                f"{provider} API key",
                type="password",
                placeholder="Paste your API key or use the placeholder in app.py",
            )
        if provider == "OpenAI":
            selected_model = st.selectbox(
                "OpenAI model",
                ["gpt-4o-mini", "gpt-4.1-mini"],
                index=0,
                help="If one model is unavailable for your key, try the other.",
            )
        elif provider == "OpenRouter":
            selected_model = st.selectbox(
                "OpenRouter model",
                ["openrouter/free", "mistralai/mistral-7b-instruct:free", "google/gemma-3-4b-it:free"],
                index=0,
                help="Use openrouter/free for the easiest free setup.",
            )
        elif provider == "Google Gemini":
            selected_model = GEMINI_MODEL
        show_api_diagnostics = st.checkbox(
            "Show API diagnostics",
            value=True,
            help="Shows the exact API error when an AI provider falls back.",
        )
        if provider != "Fallback only" and st.button("Test API Connection", use_container_width=True):
            test_response = generate_llm_response(
                user_text="This is a short connection test.",
                emotion="Happy",
                sentiment="Positive",
                provider=provider,
                api_key=api_key,
                model_name=selected_model,
            )
            if test_response.get("api_error"):
                st.error("API test failed.")
                st.caption(test_response["api_error"])
            else:
                st.success("API test succeeded.")
        st.divider()
        st.caption("Spotify mood music")
        spotify_enabled = st.checkbox("Suggest Spotify tracks", value=True)
        spotify_client_id = st.text_input(
            "Spotify Client ID",
            type="password",
            placeholder="Leave blank to use env or st.secrets",
        )
        spotify_client_secret = st.text_input(
            "Spotify Client Secret",
            type="password",
            placeholder="Leave blank to use env or st.secrets",
        )
        st.divider()
        st.caption("ML training")
        st.write(f"Training rows: {model_metadata['rows']}")
        st.write(f"Local dataset rows: {model_metadata['local_rows']}")
        if model_metadata["sources"]:
            st.write("Dataset: " + ", ".join(model_metadata["sources"]))
        else:
            st.write("Dataset: inline samples only")
        st.caption("Pipeline")
        st.write("Text cleaning -> TF-IDF -> Logistic Regression")
        st.caption("Supported emotions")
        st.write("Happy, Sad, Stress, Anxiety")
        st.caption("Free API tip")
        st.write("Choose OpenRouter with the openrouter/free model for no-cost responses.")
        st.warning(
            "MindMitra offers supportive wellness guidance only. If you feel unsafe, contact local emergency services or someone you trust immediately."
        )

    st.markdown(
        """
        <div class="hero">
            <h1>MindMitra AI - Emotion-Aware Journaling Assistant</h1>
            <p>Write freely. MindMitra saves your entries, reads emotional patterns in the background, and offers gentle support.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    journal_col, companion_col = st.columns([1.16, 0.84], gap="large")

    with journal_col:
        st.markdown("<div class='section-shell'>", unsafe_allow_html=True)
        st.markdown("<p class='section-kicker'>Today's space</p>", unsafe_allow_html=True)
        st.markdown("<h2 class='section-heading'>Write Journal Entry</h2>", unsafe_allow_html=True)
        st.markdown(
            f"<p class='soft-copy'>Saved with date and time: {datetime.now().strftime('%A, %d %B %Y - %I:%M %p')}</p>",
            unsafe_allow_html=True,
        )

        with st.form("journal_form", clear_on_submit=True):
            user_text = st.text_area(
                "What would you like to write today?",
                height=280,
                placeholder="Write about your day, thoughts, worries, wins, or anything you want to reflect on...",
            )
            save_clicked = st.form_submit_button("Save Entry", type="primary", use_container_width=True)

        if save_clicked:
            if not user_text.strip():
                st.error("Please write something before saving your journal entry.")
            elif len(user_text.strip().split()) < 3:
                st.warning("Add a little more detail so MindMitra can understand the entry better.")
            else:
                with st.spinner("Saving your journal entry and preparing a caring response..."):
                    prediction = predict_emotion(user_text, sentiment_model, emotion_model)
                    llm_response = generate_llm_response(
                        user_text=user_text,
                        emotion=prediction["emotion"],
                        sentiment=prediction["sentiment"],
                        provider=provider,
                        api_key=api_key,
                        model_name=selected_model,
                    )
                    saved_entry = save_entry(user_text, prediction, llm_response)
                    st.session_state["last_saved_entry"] = saved_entry
                    st.session_state["last_ai_response"] = llm_response
                    st.session_state["chat_messages"] = [
                        {
                            "role": "assistant",
                            "content": llm_response.get("reply", "I'm here with you. What would you like to talk about?"),
                        }
                    ]
                    st.session_state["last_chat_source"] = llm_response.get("source", "")
                    st.session_state["last_chat_error"] = llm_response.get("api_error", "")
                    entries = load_entries()

                st.success("Journal entry saved.")

        if "last_saved_entry" in st.session_state:
            latest_entry = st.session_state["last_saved_entry"]
            st.markdown("<p class='section-kicker'>Reflection</p>", unsafe_allow_html=True)
            st.markdown("<h2 class='section-heading'>MindMitra's Response</h2>", unsafe_allow_html=True)
            render_emotion_card(
                emotion=latest_entry["emotion"],
                sentiment=latest_entry["sentiment"],
                emotion_confidence=float(latest_entry["emotion_confidence"]),
                sentiment_confidence=float(latest_entry["sentiment_confidence"]),
            )
            render_ai_response(st.session_state["last_ai_response"], show_api_diagnostics)
            render_youtube_music(latest_entry["emotion"])
        else:
            st.info("Your AI reflection will appear here after you save a journal entry.")
        st.markdown("</div>", unsafe_allow_html=True)

    with companion_col:
        st.markdown("<div class='section-shell'>", unsafe_allow_html=True)
        render_chat_companion(provider, api_key, selected_model, show_api_diagnostics)
        st.markdown("</div>", unsafe_allow_html=True)

        latest_emotion = None
        if "last_saved_entry" in st.session_state:
            latest_emotion = st.session_state["last_saved_entry"]["emotion"]
        elif entries:
            latest_emotion = entries[-1]["emotion"]

        st.markdown("<div class='section-shell'>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    archive_col, insights_col = st.columns([1.05, 0.95], gap="large")

    with archive_col:
        st.markdown("<div class='section-shell'>", unsafe_allow_html=True)
        render_journal_archive(entries, show_api_diagnostics)
        st.markdown("</div>", unsafe_allow_html=True)

    with insights_col:
        st.markdown("<div class='section-shell'>", unsafe_allow_html=True)
        st.subheader("Wellness Insights")
        for insight in generate_insights(entries):
            st.info(insight)
        render_charts(entries)
        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
