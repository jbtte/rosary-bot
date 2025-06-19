#!/usr/bin/env python3
"""Audio processing for Rosary Bot"""
import os
import requests
import ssl
from config import Config


def download_audio(episode_info):
    """Download audio file if it doesn't exist"""
    try:
        os.makedirs(Config.DOWNLOAD_DIR, exist_ok=True)
        filepath = os.path.join(Config.DOWNLOAD_DIR, episode_info.filename)

        if os.path.exists(filepath):
            print(f"File {episode_info.filename} already exists")
            return filepath

        print(f"Downloading {episode_info.filename}...")
        response = requests.get(episode_info.audio_url, stream=True)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(1024 * 1024):
                if chunk:
                    f.write(chunk)

        return filepath
    except Exception as e:
        print(f"Error downloading file: {e}")
        return None


def transcribe_audio(file_path):
    """Transcribe audio using available methods"""
    transcript = None

    # Try OpenAI Whisper API first (small cost ~$0.006 per episode)
    transcript = _try_openai_whisper_api(file_path)
    if transcript:
        return transcript

    # Try local Whisper (free)
    transcript = _try_local_whisper(file_path)
    if transcript:
        return transcript

    # Try local Whisper without ffmpeg (free)
    transcript = _try_whisper_without_ffmpeg(file_path)
    if transcript:
        return transcript

    # Try SpeechRecognition as backup
    transcript = _try_speech_recognition(file_path)
    if transcript:
        return transcript

    print("All transcription methods failed")
    return None


def _try_openai_whisper_api(file_path):
    """Try OpenAI Whisper API (small cost but reliable)"""
    try:
        from openai import OpenAI
        from config import Config

        print("Using OpenAI Whisper API for transcription...")
        client = OpenAI(api_key=Config.OPENAI_API_KEY)

        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", file=audio_file
            )
        return transcript.text
    except Exception as e:
        print(f"OpenAI Whisper API error: {e}")
        return None


def _try_whisper_without_ffmpeg(file_path):
    """Try Whisper with basic audio processing"""
    try:
        import whisper

        print("Trying Whisper with basic audio processing...")

        # Disable SSL verification for model downloads
        ssl._create_default_https_context = ssl._create_unverified_context

        # Try to load audio without ffmpeg dependencies
        model = whisper.load_model(Config.WHISPER_MODEL)

        # Whisper can sometimes handle MP3 directly
        result = model.transcribe(file_path, fp16=False)
        return result["text"]

    except Exception as e:
        print(f"Whisper without ffmpeg error: {e}")
        return None


def _try_local_whisper(file_path):
    """Try transcription with local Whisper"""
    try:
        import whisper
        import warnings

        print("Using local Whisper for transcription...")

        # Suppress common warnings
        warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

        # Disable SSL verification for model downloads
        ssl._create_default_https_context = ssl._create_unverified_context

        model = whisper.load_model(Config.WHISPER_MODEL)
        result = model.transcribe(file_path, fp16=False)  # Explicitly disable FP16
        return result["text"]
    except ImportError:
        print("Local Whisper not available...")
        return None
    except Exception as e:
        print(f"Whisper error: {e}")
        return None


def _try_speech_recognition(file_path):
    """Try transcription with SpeechRecognition"""
    try:
        import speech_recognition as sr
        from pydub import AudioSegment

        print("Trying SpeechRecognition with Google Speech API...")

        # Convert MP3 to WAV
        audio = AudioSegment.from_mp3(file_path)
        wav_path = file_path.replace(".mp3", ".wav")
        audio.export(wav_path, format="wav")

        # Transcribe
        r = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data)

        # Cleanup
        os.remove(wav_path)
        return text

    except ImportError:
        print("SpeechRecognition not available...")
        return None
    except Exception as e:
        print(f"SpeechRecognition error: {e}")
        return None


def save_transcript(episode_info, transcript):
    """Save transcript to file"""
    if not Config.SAVE_TRANSCRIPTS:
        return

    try:
        transcript_filename = episode_info.filename.replace(".mp3", "_transcript.txt")
        transcript_path = os.path.join(Config.DOWNLOAD_DIR, transcript_filename)

        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(f"Episode: {episode_info.title}\n")
            f.write(f"Published: {episode_info.published_date}\n")
            f.write(f"{'='*50}\n\n")
            f.write(transcript)

        print(f"Transcript saved to: {transcript_path}")
    except Exception as e:
        print(f"Error saving transcript: {e}")
