#!/usr/bin/env python3
"""RSS feed handling for Rosary Bot"""
import requests
import feedparser
import ssl
import urllib3
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


def get_latest_episode():
    """Get the latest episode from RSS feed"""
    try:
        # Fetch RSS feed with SSL workaround
        try:
            response = requests.get(Config.RSS_URL, verify=False)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
        except Exception:
            # Fallback method
            ssl._create_default_https_context = ssl._create_unverified_context
            feed = feedparser.parse(Config.RSS_URL)

        if not feed.entries:
            return None

        # Select episode (skip intro if configured)
        if Config.SKIP_INTRO_EPISODE and len(feed.entries) > 1:
            latest = feed.entries[1]  # Skip episode 0
        else:
            latest = feed.entries[0]

        # Extract episode information
        title = latest.title.replace("/", "-").replace(":", "-").replace("?", "")
        published_date = getattr(latest, "published", "Unknown date")

        print(f"Episode: {title}")
        print(f"Published: {published_date}")

        # Check for audio enclosure
        if not hasattr(latest, "enclosures") or not latest.enclosures:
            # Try alternative audio links
            if hasattr(latest, "links"):
                for link in latest.links:
                    if hasattr(link, "type") and "audio" in link.type:
                        audio_url = link.href
                        break
                else:
                    return None
            else:
                return None
        else:
            audio_url = latest.enclosures[0].href

        filename = f"{title}.mp3"

        return EpisodeInfo(title, audio_url, published_date, filename)

    except Exception as e:
        print(f"Error fetching RSS feed: {e}")
        return None
