#!/usr/bin/env python3
"""RSS feed handling for Rosary Bot"""
import requests
import feedparser
import ssl
import urllib3
import re
from config import Config

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class EpisodeInfo:
    """Container for episode information"""

    def __init__(self, title, audio_url, published_date, filename):
        self.title = title
        self.audio_url = audio_url
        self.published_date = published_date
        self.filename = filename


def get_latest_episode(episode_number=None):
    """
    Get episode information from RSS feed.
    If episode_number is provided, attempts to fetch that specific episode
    by matching 'Day XXX' in the title.
    Otherwise, fetches the latest episode.
    """
    try:
        # Fetch RSS feed with SSL workaround
        try:
            response = requests.get(Config.RSS_URL, verify=False)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
        except Exception as e:
            print(f"Initial RSS fetch failed, attempting fallback: {e}")
            # Fallback method
            ssl._create_default_https_context = ssl._create_unverified_context
            feed = feedparser.parse(Config.RSS_URL)

        if not feed.entries:
            print("No entries found in the RSS feed.")
            return None

        selected_entry = None

        if episode_number is not None:
            print(f"Attempting to find episode 'Day {episode_number}'...")
            # Iterate through entries to find a matching episode number in the title
            for entry in feed.entries:
                title = entry.title
                match = re.search(r"Day\s*(\d+):", title)
                if match:
                    found_day_number = int(match.group(1))
                    if found_day_number == episode_number:
                        selected_entry = entry
                        print(f"Found episode: {title}")
                        break

            if not selected_entry:
                print(
                    f"Could not find episode 'Day {episode_number}'. Falling back to latest."
                )
                # Fallback to latest if the specific episode number is not found
                if Config.SKIP_INTRO_EPISODE and len(feed.entries) > 1:
                    selected_entry = feed.entries[1]
                else:
                    selected_entry = feed.entries[0]
        else:
            # Default to latest episode logic
            if Config.SKIP_INTRO_EPISODE and len(feed.entries) > 1:
                selected_entry = feed.entries[1]  # Skip episode 0
                print("Selected latest episode (skipped intro).")
            else:
                selected_entry = feed.entries[0]
                print("Selected latest episode.")

        if not selected_entry:
            print("Could not determine which episode to select.")
            return None

        # Extract episode information
        # Sanitize title for filename
        title = selected_entry.title
        # Replace characters that might cause issues in filenames
        filename_title = (
            title.replace("/", "-")
            .replace(":", "-")
            .replace("?", "")
            .replace("\\", "")
            .replace("*", "")
            .replace("<", "")
            .replace(">", "")
            .replace("|", "")
        )
        published_date = getattr(selected_entry, "published", "Unknown date")

        print(f"Episode: {title}")
        print(f"Published: {published_date}")

        audio_url = None
        # Check for audio enclosure
        if hasattr(selected_entry, "enclosures") and selected_entry.enclosures:
            audio_url = selected_entry.enclosures[0].href
        elif hasattr(selected_entry, "links"):
            # Try alternative audio links if no enclosures
            for link in selected_entry.links:
                if hasattr(link, "type") and "audio" in link.type:
                    audio_url = link.href
                    break

        if not audio_url:
            print(f"No audio URL found for episode: {title}")
            return None

        filename = f"{title}.mp3"

        return EpisodeInfo(title, audio_url, published_date, filename)

    except Exception as e:
        print(f"Error fetching RSS feed: {e}")
        return None
