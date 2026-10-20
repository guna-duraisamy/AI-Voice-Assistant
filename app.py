import os
import base64
import hashlib
from io import BytesIO

import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from gtts import gTTS

st.set_page_config(
    page_title="AI Voice Assistant",
    page_icon="🎙️",
    layout="centered"
)

_LIVE_AUDIO_RECORDER = st.components.v2.component(
    "live_audio_recorder",
    html="""
    <div class="recorder">
      <button id="record-start" type="button">Start recording</button>
      <button id="record-stop" type="button" disabled>Stop recording</button>
      <p id="record-status" role="status" aria-live="polite">Ready to record.</p>
    </div>
    """,
    css="""
    .recorder { display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem; }
    button {
      border: 1px solid var(--st-primary-color);
      border-radius: 0.5rem;
      padding: 0.5rem 0.9rem;
      color: var(--st-text-color);
      background: var(--st-secondary-background-color);
      cursor: pointer;
    }
    button:disabled { cursor: not-allowed; opacity: 0.55; }
    p { flex-basis: 100%; margin: 0.25rem 0 0; color: var(--st-text-color); }
    """,
    js="""
    const recorders = new WeakMap();

    function encodeWav(samples, sampleRate) {
      const dataBytes = samples.length * 2;
      const buffer = new ArrayBuffer(44 + dataBytes);
      const view = new DataView(buffer);
      const writeText = (offset, value) => {
        for (let i = 0; i < value.length; i += 1) {
          view.setUint8(offset + i, value.charCodeAt(i));
        }
      };

      writeText(0, "RIFF");
      view.setUint32(4, 36 + dataBytes, true);
      writeText(8, "WAVE");
      writeText(12, "fmt ");
      view.setUint32(16, 16, true);
      view.setUint16(20, 1, true);
      view.setUint16(22, 1, true);
      view.setUint32(24, sampleRate, true);
      view.setUint32(28, sampleRate * 2, true);
      view.setUint16(32, 2, true);
      view.setUint16(34, 16, true);
      writeText(36, "data");
      view.setUint32(40, dataBytes, true);

      for (let i = 0; i < samples.length; i += 1) {
        const sample = Math.max(-1, Math.min(1, samples[i]));
        view.setInt16(44 + i * 2, sample < 0 ? sample * 32768 : sample * 32767, true);
      }

      return new Uint8Array(buffer);
    }

    function toBase64(bytes) {
      let binary = "";
      for (let offset = 0; offset < bytes.length; offset += 0x8000) {
        binary += String.fromCharCode(...bytes.subarray(offset, offset + 0x8000));
      }
      return btoa(binary);
    }

    export default function(component) {
      const { parentElement, setTriggerValue } = component;
      const startButton = parentElement.querySelector("#record-start");
      const stopButton = parentElement.querySelector("#record-stop");
      const status = parentElement.querySelector("#record-status");
      if (!startButton || !stopButton || !status) return;

      let recorder = recorders.get(parentElement);
      if (!recorder) {
        recorder = { chunks: [], recording: false };
        recorders.set(parentElement, recorder);
      }
      recorder.setTriggerValue = setTriggerValue;

      startButton.onclick = async () => {
        startButton.disabled = true;
        status.textContent = "Requesting microphone access...";
        try {
          recorder.stream = await navigator.mediaDevices.getUserMedia({
            audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true }
          });
          recorder.context = new AudioContext();
          await recorder.context.resume();
          recorder.source = recorder.context.createMediaStreamSource(recorder.stream);
          recorder.processor = recorder.context.createScriptProcessor(4096, 1, 1);
          recorder.silentOutput = recorder.context.createGain();
          recorder.silentOutput.gain.value = 0;
          recorder.chunks = [];
          recorder.recording = true;

          recorder.processor.onaudioprocess = (event) => {
            if (recorder.recording) {
              recorder.chunks.push(new Float32Array(event.inputBuffer.getChannelData(0)));
            }
          };
          recorder.source.connect(recorder.processor);
          recorder.processor.connect(recorder.silentOutput);
          recorder.silentOutput.connect(recorder.context.destination);

          stopButton.disabled = false;
          status.textContent = "Recording... Click Stop recording when you are done.";
        } catch (error) {
          recorder.recording = false;
          recorder.stream?.getTracks().forEach((track) => track.stop());
          if (recorder.context && recorder.context.state !== "closed") {
            await recorder.context.close();
          }
          startButton.disabled = false;
          status.textContent = `Could not start recording: ${error.message}`;
        }
      };

      stopButton.onclick = async () => {
        if (!recorder.recording) return;
        recorder.recording = false;
        stopButton.disabled = true;
        status.textContent = "Preparing your recording...";

        const inputLength = recorder.chunks.reduce((total, chunk) => total + chunk.length, 0);
        if (inputLength === 0) {
          status.textContent = "No audio was captured. Check your microphone and try again.";
          startButton.disabled = false;
          recorder.stream.getTracks().forEach((track) => track.stop());
          await recorder.context.close();
          return;
        }

        const input = new Float32Array(inputLength);
        let offset = 0;
        for (const chunk of recorder.chunks) {
          input.set(chunk, offset);
          offset += chunk.length;
        }

        const sampleRate = 16000;
        const inputRate = recorder.context.sampleRate;
        const outputLength = Math.floor(input.length * sampleRate / inputRate);
        const resampled = new Float32Array(outputLength);
        for (let i = 0; i < outputLength; i += 1) {
          const position = i * inputRate / sampleRate;
          const left = Math.floor(position);
          const fraction = position - left;
          const right = Math.min(left + 1, input.length - 1);
          resampled[i] = input[left] * (1 - fraction) + input[right] * fraction;
        }

        recorder.processor.disconnect();
        recorder.source.disconnect();
        recorder.silentOutput.disconnect();
        recorder.stream.getTracks().forEach((track) => track.stop());
        await recorder.context.close();
        recorder.chunks = [];

        const wav = encodeWav(resampled, sampleRate);
        recorder.setTriggerValue("recording", toBase64(wav));
        status.textContent = "Recording received. You can record another question.";
        startButton.disabled = false;
      };
    }
    """,
)

load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    st.error("GROQ_API_KEY was not found in the .env file.")
    st.stop()

client = Groq(api_key=groq_api_key)

def generate_ai_response(question, conversation_history):
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful AI voice assistant. "
                "Always answer clearly and concisely in English. "
                "Use the conversation history to understand follow-up questions."
            )
        }
    ]
    messages.extend(
        {
            "role": message["role"],
            "content": message["content"]
        }
        for message in conversation_history[-20:]
    )
    messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    chat_completion = client.chat.completions.create(
        messages=messages,
        model="openai/gpt-oss-120b",
        temperature=0.3,
        max_tokens=300
    )

    return chat_completion.choices[0].message.content

def convert_text_to_speech(text):
    audio_buffer = BytesIO()

    speech = gTTS(
        text=text,
        lang="en"
    )

    speech.write_to_fp(audio_buffer)
    audio_buffer.seek(0)

    return audio_buffer

st.title("🎙️ AI Voice Assistant")

st.write(
    "Ask a question using your voice, "
    "and the AI assistant will respond."
)

st.write("Record a question using your microphone, then stop when you are done.")
recording_result = _LIVE_AUDIO_RECORDER(
    key="live_audio_recorder",
    on_recording_change=lambda: None,
)
st.session_state.setdefault("conversation_history", [])
st.session_state.setdefault("last_processed_recording", None)
st.session_state.setdefault("pending_recording_id", None)
st.session_state.setdefault("transcript_to_send", "")
if st.button("Clear conversation"):
    st.session_state.conversation_history.clear()

if recording_result.recording:
    audio_bytes = base64.b64decode(recording_result.recording, validate=True)

    if not audio_bytes:
        st.warning(
            "No audio was recorded. Please check microphone access and try again."
        )
        st.stop()
    st.audio(audio_bytes, format="audio/wav")
    recording_id = hashlib.sha256(audio_bytes).hexdigest()
    if (
        recording_id != st.session_state.last_processed_recording
        and recording_id != st.session_state.pending_recording_id
    ):
        try:
            with st.spinner("Converting speech to text..."):
                transcription = client.audio.transcriptions.create(
                    file=(
                        "recording.wav",
                        audio_bytes,
                    ),
                    model="whisper-large-v3",
                    language="en",
                    prompt=(
                        "The audio is an English question about technology. "
                        "Technical terms may include neural network, machine learning, "
                        "deep learning, and artificial intelligence."
                    ),
                    response_format="json",
                    temperature=0.0
                )
        except Exception:
            st.error(
                "Unable to transcribe the recording. "
                "Please check your connection and try again."
            )
            st.stop()
        st.session_state.transcript_to_send = getattr(
            transcription,
            "text",
            ""
        ).strip()
        st.session_state.pending_recording_id = recording_id

    if st.session_state.pending_recording_id == recording_id:
        with st.form("transcript_review"):
            st.write("Check the transcript. Correct it if needed, then send it.")
            st.text_area(
                "Transcript",
                key="transcript_to_send"
            )
            send_question = st.form_submit_button("Send to assistant")

        if send_question:
            transcribed_text = st.session_state.transcript_to_send.strip()
            if not transcribed_text:
                st.warning("Enter or correct your question before sending it.")
                st.stop()

            with st.spinner("Generating AI response..."):
                ai_response = generate_ai_response(
                    transcribed_text,
                    st.session_state.conversation_history
                )

            if not ai_response or not ai_response.strip():
                st.error(
                    "The assistant could not generate a response. "
                    "Please try asking the question again."
                )
                st.stop()

            with st.spinner("Generating voice response..."):
                response_audio = convert_text_to_speech(
                    ai_response
                )
            st.session_state.conversation_history.extend(
                [
                    {
                        "role": "user",
                        "content": transcribed_text
                    },
                    {
                        "role": "assistant",
                        "content": ai_response,
                        "audio": response_audio.getvalue()
                    }
                ]
            )
            st.session_state.last_processed_recording = recording_id
            st.session_state.pending_recording_id = None
            st.session_state.transcript_to_send = ""
            st.rerun()

if st.session_state.conversation_history:
    st.subheader("Conversation")
    for message in st.session_state.conversation_history:
        if message["role"] == "user":
            st.markdown("**You asked**")
            st.write(message["content"])
        else:
            st.markdown("**AI Assistant**")
            st.write(message["content"])
            st.audio(
                BytesIO(message["audio"]),
                format="audio/mp3"
            )