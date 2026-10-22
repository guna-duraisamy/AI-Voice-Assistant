# AI Voice Assistant

A beginner-friendly AI Voice Assistant built with Python and Streamlit.

This app lets you:
- record a spoken question
- convert speech to text
- send the text to an AI model
- generate a spoken response
- play the answer back inside the app

This project is part of the AI Projects Series by Karthik's Show.

---

## Overview

The AI Voice Assistant follows a simple pipeline:

```text
Voice Input
   ↓
Speech-to-Text (Whisper)
   ↓
AI Response Generation (Groq LLM)
   ↓
Text-to-Speech (gTTS)
   ↓
Spoken Answer
```

This project is a great introduction to:
- microphone input in web apps
- speech recognition
- LLM integration
- text-to-speech generation
- building interactive AI apps with Streamlit

---

## Tech Stack

- Python
- Streamlit — UI and microphone input
- Groq Whisper — speech-to-text
- Groq LLM — AI response generation
- gTTS — text-to-speech
- GitHub Copilot — code review and testing suggestions

---

## Project Structure

```text
ai-voice-assistant/
├── app.py
├── requirements.txt
├── .env
├── .gitignore
├── README.md
└── venv/           (created locally)
```

---

## Prerequisites

Before running the app, make sure you have:

- Python 3.9 or later
- A modern web browser
- Microphone access enabled in the browser
- A Groq API key

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/KarthiksShow/ai-voice-assistant
cd ai-voice-assistant
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Activate it on macOS or Linux:

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Important:
- never commit the `.env` file to GitHub
- keep your API key private

Add the following to `.gitignore`:

```text
.env
venv/
__pycache__/
```

---

## Run the Application

```bash
streamlit run app.py
```

Then open the local URL shown in the terminal and allow microphone access when prompted.

---

## How It Works

1. The user speaks a question into the microphone.
2. The audio is captured by the Streamlit app.
3. Whisper converts the spoken audio into text.
4. The transcribed text is sent to a Groq large language model.
5. The AI generates a response.
6. The response is converted into speech using gTTS.
7. The spoken answer is played back in the app.

---

## Example Questions

Try asking:

```text
What are three benefits of learning Python?
```

```text
Explain artificial intelligence in simple words.
```

```text
What is the difference between AI and machine learning?
```

```text
Give me three tips for learning programming.
```

---

## Prompt Templates Used

### 1. Voice Assistant System Prompt

This prompt defines how the assistant should answer user questions.

```text
You are a helpful AI voice assistant.
Answer clearly and concisely using simple language.
```

Python example:

```python
messages = [
    {
        "role": "system",
        "content": (
            "You are a helpful AI voice assistant. "
            "Answer clearly and concisely using simple language."
        )
    },
    {
        "role": "user",
        "content": question
    }
]
```

---

### 2. Reusable Voice Assistant Prompt Template

```text
You are a [ROLE].

Answer the user's question using:
- Audience: [TARGET AUDIENCE]
- Tone: [TONE]
- Detail level: [SHORT / MEDIUM / DETAILED]
- Language: [LANGUAGE]

Keep the answer suitable for spoken output.
Avoid unnecessary formatting and overly long responses.

User question:
[TRANSCRIBED QUESTION]
```

Example:

```text
You are a beginner-friendly technology teacher.

Answer the user's question using:
- Audience: Beginners
- Tone: Friendly and conversational
- Detail level: Short
- Language: English

Keep the answer suitable for spoken output.
Avoid unnecessary formatting and overly long responses.

User question:
Explain machine learning in simple words.
```

---

### 3. GitHub Copilot Software Tester Prompt

```text
Review this AI Voice Assistant application as a software tester.

Identify important edge cases and failure scenarios related to:
- microphone recording
- empty or silent audio
- speech transcription
- Groq API failures
- empty AI responses
- text-to-speech errors

Do not rewrite the entire application.

Suggest only practical improvements that are suitable for a beginner project,
and explain why each one is useful.
```

---

### 4. General Copilot Code Review Template

```text
Review this [APPLICATION TYPE] as a [REVIEWER ROLE].

Focus on:
- [AREA 1]
- [AREA 2]
- [AREA 3]
- error handling
- user experience

Do not rewrite the entire application.

List the most important issues first.
Suggest beginner-friendly improvements and explain why each one is useful.
```

