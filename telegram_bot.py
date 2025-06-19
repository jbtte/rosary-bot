#!/usr/bin/env python3
"""Telegram bot functionality for Rosary Bot"""
import requests
from config import Config


def send_summary(episode_info, summary):
    """Send summary to Telegram"""
    try:
        # Format the message
        message = _format_telegram_message(episode_info, summary)

        # Send to Telegram
        success = _send_telegram_message(message)

        if success:
            print("✅ Summary sent to Telegram successfully!")
            return True
        else:
            print("❌ Failed to send to Telegram")
            return False

    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False


def _clean_message_for_telegram(text):
    """Clean message content to avoid Telegram formatting issues"""
    # Replace problematic characters that can break Markdown
    text = text.replace("_", "\\_")  # Escape underscores
    text = text.replace("*", "\\*")  # Escape asterisks that aren't bold markers
    text = text.replace("[", "\\[")  # Escape square brackets
    text = text.replace("]", "\\]")  # Escape square brackets
    text = text.replace("`", "\\`")  # Escape backticks

    # Fix bold markers - restore intended bold formatting
    text = text.replace("\\*\\*", "**")  # Restore double asterisks for bold

    return text


def _format_telegram_message(episode_info, summary):
    """Format the message for Telegram"""
    # Clean the summary for Telegram
    clean_summary = _clean_message_for_telegram(summary)

    # Create header with episode info
    header = f"""🔮 **{episode_info.title}**
📅 {episode_info.published_date}

"""

    # Combine header with summary
    full_message = header + clean_summary

    # Ensure message doesn't exceed Telegram's limit (4096 characters)
    if len(full_message) > 4096:
        # Calculate how much space we have for the summary
        available_space = 4096 - len(header) - 100  # Leave some buffer

        # Truncate summary if needed
        if len(clean_summary) > available_space:
            clean_summary = (
                clean_summary[:available_space]
                + "\n\n*[Summary truncated due to length]*"
            )

        full_message = header + clean_summary

    return full_message


def _send_telegram_message(text):
    """Send message to Telegram API"""
    try:
        url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"

        payload = {
            "chat_id": Config.TELEGRAM_USER_ID,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }

        response = requests.post(url, data=payload, timeout=30)

        if response.status_code == 400:
            # Handle markdown parsing errors
            error_info = response.json() if response.text else {}
            error_desc = error_info.get("description", "")

            if "can't parse" in error_desc.lower() or "markdown" in error_desc.lower():
                print("⚠️  Markdown parsing issue, sending as plain text...")
                payload["parse_mode"] = None
                response = requests.post(url, data=payload, timeout=30)

        response.raise_for_status()

        # Check if Telegram API returned success
        result = response.json()
        if result.get("ok"):
            return True
        else:
            print(
                f"❌ Telegram API error: {result.get('description', 'Unknown error')}"
            )
            return False

    except requests.exceptions.Timeout:
        print("❌ Telegram request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Telegram request error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Telegram error: {e}")
        return False


def test_telegram_connection():
    """Test Telegram bot connection"""
    try:
        print("🧪 Testing Telegram connection...")

        url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=10)

        if response.status_code == 401:
            print("❌ 401 Unauthorized - Bot token is invalid")
            print("🔧 Please check your bot token in .env file")
            return False

        response.raise_for_status()

        result = response.json()
        if result.get("ok"):
            bot_info = result.get("result", {})
            print(
                f"✅ Connected to Telegram bot: {bot_info.get('first_name', 'Unknown')} (@{bot_info.get('username', 'Unknown')})"
            )
            return True
        else:
            print(
                f"❌ Telegram bot test failed: {result.get('description', 'Unknown error')}"
            )
            return False

    except Exception as e:
        print(f"❌ Telegram connection test error: {e}")
        return False


def send_test_message():
    """Send a test message to verify everything works"""
    test_message = """🧪 **Rosary Bot Test Message**

This is a test to verify the Telegram integration is working correctly.

✅ If you receive this message, everything is set up properly!"""

    return _send_telegram_message(test_message)


# Utility function for standalone testing
if __name__ == "__main__":
    print("Testing Telegram Bot...")

    # Test connection
    if test_telegram_connection():
        # Send test message
        if send_test_message():
            print("✅ All Telegram tests passed!")
        else:
            print("❌ Test message failed")
    else:
        print("❌ Connection test failed")
