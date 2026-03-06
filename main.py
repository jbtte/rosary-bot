#!/usr/bin/env python3
"""
Rosary Bot - Main Script
Downloads, transcribes, and summarizes Catholic homilies
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from rss_handler import get_latest_episode
from audio_processor import download_audio, transcribe_audio, save_transcript
from summarizers import create_summary
from telegram_bot import send_summary
from cleanup import cleanup_episode_files


def main():
    """Main execution flow"""
    print("🔮 Rosary Bot Starting...")

    episode_number = None
    # Check if an episode number is provided as a command-line argument
    if len(sys.argv) > 1:
        try:
            episode_number = int(sys.argv[1])
            print(f"\n📡 Fetching episode number: {episode_number}...")
        except ValueError:
            print(
                f"⚠️ Invalid episode number provided: '{sys.argv[1]}'. Falling back to latest episode."
            )
            episode_number = None
    else:
        print("\n📡 Fetching latest episode...")

    # Step 1: Get episode info
    # Pass the episode_number if it's set, otherwise get_latest_episode will fetch the latest
    episode_info = get_latest_episode(episode_number=episode_number)
    if not episode_info:
        print("❌ No episode found.")
        return False

    # Step 2: Download audio file
    print(f"\n⬇️  Downloading: {episode_info.filename}")
    audio_file = download_audio(episode_info)
    if not audio_file:
        print("❌ Failed to download audio.")
        return False

    # Step 3: Transcribe audio
    print("\n🎤 Transcribing audio...")
    transcript = transcribe_audio(audio_file)
    if not transcript:
        print("❌ Failed to transcribe audio.")
        return False

    # Step 4: Save transcript
    save_transcript(episode_info, transcript)

    # Step 5: Create summary
    ## Não rodando o resumo por enquanto ##
    # print("\n📝 Creating summary...")
    # summary = create_summary(transcript, episode_info)
    # if not summary:
    #     print("❌ Failed to create summary.")
    #     return False

    # Step 6: Send to Telegram
    ## Como está sem resumo, não envia ##
    # print("\n📱 Sending to Telegram...")
    # success = send_summary(episode_info, summary)

    success = True  # Simulate success for now

    if success:
        # Não rodando o envio por enquanto
        # print("✅ Summary sent successfully to Telegram!")

        # Step 7: Cleanup files after successful completion
        print("\n🧹 Cleaning up files...")
        cleanup_episode_files(episode_info)

        print("✅ Done! Process completed successfully.")
        return True
    else:
        print("⚠️  Summary created but failed to send to Telegram.")
        print("📁 Files preserved for manual review.")
        print(f"Summary:\n{summary}")
        return False


if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        exit(1)
