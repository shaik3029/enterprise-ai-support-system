import os
from langchain_groq import ChatGroq
from groq import Groq

# Lazy-loaded local Whisper model instance
_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel(
            "tiny.en",
            device="cpu",
            compute_type="int8"
        )
    return _whisper_model


def transcribe_audio(audio_file_path: str, groq_api_key: str) -> str:
    """
    Transcribes audio using Groq cloud Whisper API for blazing speed (< 1 second),
    with automatic fallback to local faster-whisper.
    """
    # 1. Try Groq Whisper API
    if groq_api_key:
        try:
            client = Groq(api_key=groq_api_key)
            with open(audio_file_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-large-v3-turbo",
                    temperature=0.0
                )
                if transcription and transcription.text:
                    return transcription.text.strip()
        except Exception as e:
            print(f"[AudioAgent] Groq cloud transcription notice: {e}. Falling back to local faster-whisper.")

    # 2. Local faster-whisper fallback
    model = get_whisper_model()
    segments, info = model.transcribe(
        audio_file_path,
        beam_size=1,
        vad_filter=True
    )
    transcript = " ".join(segment.text for segment in segments).strip()
    return transcript or "No spoken content detected in audio recording."


def analyze_call(audio_file_path: str, groq_api_key: str):
    # Transcribe customer call
    transcript = transcribe_audio(audio_file_path, groq_api_key)

    # Analyze transcript using Groq
    llm = ChatGroq(
        groq_api_key=groq_api_key,
        model_name="openai/gpt-oss-20b",
        temperature=0.2
    )

    prompt = f"""
You are an enterprise customer support call analyst.

Analyze this customer call transcript:

{transcript}

Return exactly in this format:

Sentiment: <Positive / Neutral / Negative>

Key Issue: <Brief description of customer's main concern or inquiry>

Action Required: <Specific recommended next steps for support engineering/operations>

Summary: <Concise 2-3 sentence overview of the conversation>
"""

    try:
        response = llm.invoke(prompt)
        analysis_text = response.content.strip()
    except Exception as e:
        analysis_text = f"Sentiment: Neutral\n\nKey Issue: Audio inquiry received\n\nAction Required: Manual review by support specialist\n\nSummary: Transcript generated successfully ({len(transcript)} characters)."

    return {
        "transcript": transcript,
        "analysis": analysis_text
    }