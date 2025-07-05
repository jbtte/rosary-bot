#!/usr/bin/env python3
"""File cleanup management for Rosary Bot"""
import os
import shutil
from config import Config


def cleanup_episode_files(episode_info):
    """Delete audio, transcript, and summary files after successful completion"""
    if not Config.CLEANUP_FILES:
        print("🔒 File cleanup disabled in config")
        return False

    try:
        # Move transcript to Downloads folder first
        transcript_moved = _move_transcript_to_downloads(episode_info)

        # Delete other files
        files_to_delete = _get_episode_files(episode_info)
        deleted_files = _delete_files(files_to_delete)

        if deleted_files or transcript_moved:
            deleted_count = len(deleted_files)
            if transcript_moved:
                print(
                    f"✅ Cleanup completed - removed {len(deleted_files)} files, moved transcript to Downloads"
                )
            else:
                print(f"✅ Cleanup completed - removed {deleted_count} files")
            return True
        else:
            print("ℹ️  No files to clean up")
            return False

    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return False


def _move_transcript_to_downloads(episode_info):
    """Move transcript file to computer's Downloads folder"""
    try:
        transcript_filename = episode_info.filename.replace(".mp3", "_transcript.txt")
        source_path = os.path.join(Config.DOWNLOAD_DIR, transcript_filename)

        if not os.path.exists(source_path):
            return False

        # Destination is user's Downloads folder
        downloads_folder = os.path.expanduser("~/Downloads")
        destination_path = os.path.join(downloads_folder, transcript_filename)

        # Move the file
        shutil.move(source_path, destination_path)
        print(f"📄 Moved transcript to: {destination_path}")
        return True

    except Exception as e:
        print(f"⚠️  Could not move transcript: {e}")
        return False


def _get_episode_files(episode_info):
    """Get list of all files related to an episode"""
    files_to_check = []

    # Audio file
    audio_file = os.path.join(Config.DOWNLOAD_DIR, episode_info.filename)
    files_to_check.append(audio_file)

    # Summary files (all possible types)
    summary_types = ["gpt", "chatgpt_web", "simple"]
    for summary_type in summary_types:
        summary_file = os.path.join(
            Config.DOWNLOAD_DIR,
            episode_info.filename.replace(".mp3", f"_summary_{summary_type}.txt"),
        )
        files_to_check.append(summary_file)

    # Return only files that actually exist
    existing_files = [f for f in files_to_check if os.path.exists(f)]
    return existing_files


def _delete_files(file_list):
    """Delete a list of files and return successfully deleted files"""
    deleted_files = []

    for file_path in file_list:
        try:
            os.remove(file_path)
            filename = os.path.basename(file_path)
            print(f"🗑️  Deleted: {filename}")
            deleted_files.append(file_path)
        except Exception as e:
            filename = os.path.basename(file_path)
            print(f"⚠️  Could not delete {filename}: {e}")

    return deleted_files


def cleanup_transcripts(days_old=30):
    """Clean up transcript files from Downloads folder older than specified days"""
    if not Config.CLEANUP_FILES:
        print("🔒 File cleanup disabled in config")
        return False

    try:
        import time

        current_time = time.time()
        cutoff_time = current_time - (days_old * 24 * 60 * 60)

        if not os.path.exists(Config.TRANSCRIPT_DIR):
            return False

        old_transcripts = []
        for filename in os.listdir(Config.TRANSCRIPT_DIR):
            # Look for Rosary Bot transcript files specifically
            if filename.endswith("_transcript.txt") and "Day " in filename:
                file_path = os.path.join(Config.TRANSCRIPT_DIR, filename)

                # Check if file is older than cutoff
                file_time = os.path.getmtime(file_path)
                if file_time < cutoff_time:
                    old_transcripts.append(file_path)

        if old_transcripts:
            deleted_files = _delete_files(old_transcripts)
            print(
                f"📄 Transcript cleanup: removed {len(deleted_files)} old transcripts from Downloads (>{days_old} days)"
            )
            return len(deleted_files) > 0
        else:
            print(
                f"ℹ️  No old Rosary Bot transcripts found in Downloads (>{days_old} days)"
            )
            return False

    except Exception as e:
        print(f"❌ Error during transcript cleanup: {e}")
        return False


def cleanup_old_files(days_old=7):
    """Clean up files older than specified days (optional maintenance function)"""
    if not Config.CLEANUP_FILES:
        print("🔒 File cleanup disabled in config")
        return False

    try:
        import time

        current_time = time.time()
        cutoff_time = current_time - (
            days_old * 24 * 60 * 60
        )  # Convert days to seconds

        if not os.path.exists(Config.DOWNLOAD_DIR):
            return False

        old_files = []
        for filename in os.listdir(Config.DOWNLOAD_DIR):
            file_path = os.path.join(Config.DOWNLOAD_DIR, filename)

            # Skip directories
            if os.path.isdir(file_path):
                continue

            # Check if file is older than cutoff
            file_time = os.path.getmtime(file_path)
            if file_time < cutoff_time:
                old_files.append(file_path)

        if old_files:
            deleted_files = _delete_files(old_files)
            print(
                f"🧹 Maintenance cleanup: removed {len(deleted_files)} old files (>{days_old} days)"
            )
            return len(deleted_files) > 0
        else:
            print(f"ℹ️  No old files found (>{days_old} days)")
            return False

    except Exception as e:
        print(f"❌ Error during maintenance cleanup: {e}")
        return False


def get_storage_info():
    """Get information about files in the download directory"""
    try:
        if not os.path.exists(Config.DOWNLOAD_DIR):
            return {"total_files": 0, "total_size": 0, "file_types": {}}

        total_files = 0
        total_size = 0
        file_types = {}

        for filename in os.listdir(Config.DOWNLOAD_DIR):
            file_path = os.path.join(Config.DOWNLOAD_DIR, filename)

            # Skip directories
            if os.path.isdir(file_path):
                continue

            total_files += 1
            file_size = os.path.getsize(file_path)
            total_size += file_size

            # Track file types
            extension = os.path.splitext(filename)[1].lower()
            file_types[extension] = file_types.get(extension, 0) + 1

        return {
            "total_files": total_files,
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_types": file_types,
        }

    except Exception as e:
        print(f"❌ Error getting storage info: {e}")
        return {"total_files": 0, "total_size": 0, "file_types": {}}


def cleanup_debug_files():
    """Clean up any debug files created during development"""
    try:
        import shutil

        debug_dirs = [
            os.path.join(
                os.path.dirname(__file__), "bin"
            ),  # Remove debug bin directory
        ]

        for debug_dir in debug_dirs:
            if os.path.exists(debug_dir):
                shutil.rmtree(debug_dir)
                print(f"🧹 Removed debug directory: {os.path.basename(debug_dir)}")

    except Exception as e:
        print(f"⚠️  Error cleaning debug files: {e}")


# Utility function for standalone testing
cleanup_debug_files()
if __name__ == "__main__":
    print("📊 Storage Information:")
    info = get_storage_info()
    print(f"Total files: {info['total_files']}")
    print(f"Total size: {info['total_size_mb']} MB")
    print(f"File types: {info['file_types']}")

    # Uncomment to test cleanup of old files
    # cleanup_old_files(days_old=1)
