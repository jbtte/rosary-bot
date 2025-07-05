#!/usr/bin/env python3
"""
Test ChatGPT Web Automation
Use an existing transcript to test the ChatGPT automation
"""
import os
import sys
from config import Config
from summarizers import _try_chatgpt_web


def test_chatgpt_with_transcript():
    """Test ChatGPT automation with an existing transcript"""

    # Look for transcript files in downloads folder
    transcript_files = []
    if os.path.exists(Config.DOWNLOAD_DIR):
        for filename in os.listdir(Config.DOWNLOAD_DIR):
            if filename.endswith("_transcript.txt"):
                transcript_files.append(filename)

    # Also check user's Downloads folder
    user_downloads = os.path.expanduser("~/Downloads")
    if os.path.exists(user_downloads):
        for filename in os.listdir(user_downloads):
            if filename.endswith("_transcript.txt") and "Day " in filename:
                transcript_files.append(os.path.join(user_downloads, filename))

    if not transcript_files:
        print("❌ No transcript files found!")
        print("Please make sure you have a transcript file in:")
        print(f"  - {Config.DOWNLOAD_DIR}/")
        print(f"  - {user_downloads}/")
        print("Transcript files should end with '_transcript.txt'")
        return

    # Show available transcripts
    print("📄 Available transcript files:")
    for i, filename in enumerate(transcript_files, 1):
        display_name = os.path.basename(filename)
        print(f"  {i}. {display_name}")

    # Let user choose
    try:
        choice = input(
            f"\nChoose a transcript (1-{len(transcript_files)}) or press Enter for the first one: "
        ).strip()
        if not choice:
            choice = "1"

        index = int(choice) - 1
        if index < 0 or index >= len(transcript_files):
            print("❌ Invalid choice!")
            return

        selected_file = transcript_files[index]
        if not os.path.isabs(selected_file):
            selected_file = os.path.join(Config.DOWNLOAD_DIR, selected_file)

    except (ValueError, KeyboardInterrupt):
        print("❌ Invalid choice or cancelled!")
        return

    # Read the transcript
    try:
        print(f"\n📖 Reading: {os.path.basename(selected_file)}")
        with open(selected_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract just the transcript content (skip the header)
        if "=" * 50 in content:
            transcript = content.split("=" * 50, 1)[1].strip()
        else:
            transcript = content

        print(f"📊 Transcript length: {len(transcript)} characters")
        print(f"📝 Preview: {transcript[:200]}...")

    except Exception as e:
        print(f"❌ Error reading transcript: {e}")
        return

    # Test ChatGPT automation
    print(f"\n🌐 Testing ChatGPT web automation...")
    print("💡 This will open a browser window - make sure you're logged into ChatGPT")

    try:
        summary = _try_chatgpt_web(transcript)

        if summary:
            print(f"\n✅ SUCCESS! ChatGPT automation worked!")
            print(f"📄 Summary length: {len(summary)} characters")
            print(f"\n📋 Generated Summary:")
            print("=" * 60)
            print(summary)
            print("=" * 60)

            # Save the test summary
            test_summary_file = selected_file.replace(
                "_transcript.txt", "_test_summary_chatgpt.txt"
            )
            try:
                with open(test_summary_file, "w", encoding="utf-8") as f:
                    f.write(f"Test Summary via ChatGPT Web Automation\n")
                    f.write(f"Source: {os.path.basename(selected_file)}\n")
                    f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"{'='*60}\n\n")
                    f.write(summary)
                print(
                    f"\n💾 Test summary saved to: {os.path.basename(test_summary_file)}"
                )
            except Exception as save_e:
                print(f"⚠️  Could not save summary: {save_e}")

        else:
            print(f"\n❌ ChatGPT automation failed!")
            print("💡 This could be due to:")
            print("   - Login issues")
            print("   - Interface changes")
            print("   - Network problems")
            print("   - Browser compatibility")

    except KeyboardInterrupt:
        print(f"\n👋 Test cancelled by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback

        traceback.print_exc()


def list_available_transcripts():
    """List all available transcript files"""
    print("📄 Available transcript files:")

    locations = [Config.DOWNLOAD_DIR, os.path.expanduser("~/Downloads")]

    total_found = 0
    for location in locations:
        if not os.path.exists(location):
            continue

        files = [f for f in os.listdir(location) if f.endswith("_transcript.txt")]
        if files:
            print(f"\n📁 In {location}:")
            for filename in sorted(files):
                print(f"   • {filename}")
                total_found += 1

    if total_found == 0:
        print("❌ No transcript files found!")
        print("\n💡 To create a transcript file, run the main bot:")
        print("   python main.py")
    else:
        print(f"\n✅ Found {total_found} transcript file(s)")


if __name__ == "__main__":
    import time

    print("🧪 ChatGPT Web Automation Tester")
    print("=" * 40)

    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_available_transcripts()
    else:
        test_chatgpt_with_transcript()
