#!/usr/bin/env python3
"""Summarization methods for Rosary Bot"""
import re
import time
import os
from openai import OpenAI
from config import Config

# Initialize OpenAI client
client = OpenAI(api_key=Config.OPENAI_API_KEY)


def _extract_meditation_content(transcript):
    """Extract only the meditation content, skipping the daily introduction"""
    try:
        # Primary marker that Father Mark-Mary uses to start meditation
        primary_marker = "today we'll be meditating"

        # Additional backup markers in case of transcription variations
        backup_markers = [
            "today we will be meditating",
            "today we're meditating",
            "today we are meditating",
            "we'll be meditating",
            "we will be meditating",
            "let us meditate",
            "we meditate on",
            "today's meditation",
        ]

        # Convert to lowercase for searching
        transcript_lower = transcript.lower()

        # First, try to find the primary marker
        pos = transcript_lower.find(primary_marker)
        if pos != -1:
            # Start from the beginning of this sentence
            meditation_content = transcript[pos:].strip()
            print(f"✂️ Found '{primary_marker}' at position {pos}")
            return meditation_content

        # Try backup markers
        for marker in backup_markers:
            pos = transcript_lower.find(marker)
            if pos != -1:
                meditation_content = transcript[pos:].strip()
                print(f"✂️  Found '{marker}' at position {pos}")
                return meditation_content

        # If no specific marker found, skip first 25% (likely introduction)
        skip_length = len(transcript) // 4
        meditation_content = transcript[skip_length:].strip()
        print(f"✂️  No meditation marker found, skipping first {skip_length} characters")
        return meditation_content

    except Exception as e:
        print(f"⚠️  Error extracting meditation content: {e}")
        return transcript  # Return full transcript as fallback


def _extract_artwork_info(text):
    """Extract artwork and artist information from the meditation text"""
    try:
        text_lower = text.lower()

        # Common patterns for artwork mentions
        artwork_patterns = [
            r"painting\s+(?:by\s+|from\s+)?([^.]+)",
            r"artwork\s+(?:by\s+|from\s+)?([^.]+)",
            r"image\s+(?:by\s+|from\s+)?([^.]+)",
            r"(?:the\s+)?([^.]+)\s+by\s+([^.]+)",
            r"artist\s+([^.]+)",
        ]

        # Look for artwork mentions
        for pattern in artwork_patterns:
            match = re.search(pattern, text_lower)
            if match:
                artwork_text = match.group(0)
                # Clean up the text
                artwork_text = (
                    artwork_text.replace("painting", "")
                    .replace("artwork", "")
                    .replace("image", "")
                )
                artwork_text = re.sub(r"\s+", " ", artwork_text).strip()

                if len(artwork_text) > 5:  # Avoid too short matches
                    return f"Artwork: {artwork_text.title()}"

        return None

    except Exception as e:
        return None


def _get_summary_prompt(transcript, max_length=4000):
    """Generate the summarization prompt focused on meditation content"""
    # Extract only the meditation content
    meditation_content = _extract_meditation_content(transcript)

    # Truncate if too long
    if len(meditation_content) > max_length:
        meditation_content = meditation_content[:max_length] + "..."

    return f"""Please summarize ONLY the meditation/rosary content from this Catholic homily, ignoring any repetitive daily introduction.

You will receive a transcript of a Catholic spiritual podcast. Your task is to create a concise summary, faithful to the speaker's words.
    
Format requirements:
* First bullet: If an artwork/painting and artist are mentioned, include that (e.g., "Artwork: The Annunciation by Fra Angelico"). If no artwork mentioned, skip this bullet.
• Then give up to 8 bullet points with the main spiritual insights or practical teachings (each ≤150 characters).
• Use the speaker's wording or faithful paraphrasing. Do not add interpretations or go into theology not mentioned.
• You may include new ideas only if they help clarify or summarize the speaker's points — no theological digressions.
• Avoid repeating ideas. Each bullet must be distinct.
• End with the practical reflection, if the speaker gives one. Place it in italics.

Structure:
* Start with artwork info (if mentioned)
* Bullets 2–9: Key insights (max 8)
* Final line: Practical reflection (in italics)

Output Example:
Artwork: The Annunciation by Fra Angelico
– God often speaks in silence and stillness
– Mary's “yes” came from humility and trust
– Obedience opens the door to grace
– Silence is a posture of receptivity
– Faith means saying yes without full clarity
– God initiates; we respond
– Grace builds on openness, not control
– Mary shows the power of quiet surrender
Spend time in silence today, listening for God's invitation

MEDITATION CONTENT:
{meditation_content}"""


def _save_summary_to_file(episode_info, summary, method_type):
    """Save summary to a text file"""
    if not Config.SAVE_SUMMARIES:
        return

    try:
        # Create filename with method type
        summary_filename = episode_info.filename.replace(
            ".mp3", f"_summary_{method_type}.txt"
        )
        summary_path = os.path.join(Config.DOWNLOAD_DIR, summary_filename)

        # Create downloads directory if it doesn't exist
        os.makedirs(Config.DOWNLOAD_DIR, exist_ok=True)

        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(f"Episode: {episode_info.title}\n")
            f.write(f"Published: {episode_info.published_date}\n")
            f.write(f"Summary Method: {method_type.upper()}\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*60}\n\n")
            f.write(summary)

        print(f"📄 Summary saved to: {summary_path}")

    except Exception as e:
        print(f"❌ Error saving summary: {e}")


def create_summary(transcript, episode_info=None):
    """Create summary using available methods with fallbacks"""

    # Try OpenAI API first
    summary = _try_openai_api(transcript)
    if summary:
        # Save GPT summary to file
        if episode_info:
            _save_summary_to_file(episode_info, summary, "gpt")
        return summary

    # Try ChatGPT web automation
    summary = _try_chatgpt_web(transcript)
    if summary:
        # Save ChatGPT web summary to file
        if episode_info:
            _save_summary_to_file(episode_info, summary, "chatgpt_web")
        return summary

    # Fallback to simple extractive summary
    print("All AI methods failed. Creating simple summary...")
    summary = _create_simple_summary(transcript)
    if episode_info:
        _save_summary_to_file(episode_info, summary, "simple")
    return summary


def _try_openai_api(transcript):
    """Try summarization with OpenAI API"""
    try:
        prompt = _get_summary_prompt(transcript)

        # Try different models in order of preference
        for model in Config.OPENAI_MODELS:
            try:
                print(f"Using OpenAI model: {model}")
                completion = client.chat.completions.create(
                    model=model, messages=[{"role": "user", "content": prompt}]
                )
                print(f"✅ Successfully used model: {model}")
                return completion.choices[0].message.content
            except Exception as model_error:
                if "does not exist" in str(model_error) or "model_not_found" in str(
                    model_error
                ):
                    print(f"❌ Model {model} not available")
                    continue
                elif "quota" in str(model_error).lower() or "429" in str(model_error):
                    print(f"❌ Quota exceeded for {model}")
                    continue
                else:
                    print(f"❌ Error with {model}: {model_error}")
                    continue

        print("❌ No OpenAI models available")
        return None

    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        return None


def _try_chatgpt_web(transcript):
    """Try summarization with ChatGPT web automation"""
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager

        print("🌐 Trying ChatGPT web automation...")

        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # Use webdriver-manager to automatically download ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Execute script to hide webdriver property
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        try:
            print("Opening ChatGPT...")
            driver.get(Config.CHATGPT_URL)
            time.sleep(5)

            # Check if we need to log in
            try:
                login_button = driver.find_element(
                    By.XPATH, "//button[contains(text(), 'Log in')]"
                )
                print("🔐 Please log in to ChatGPT in the browser window.")
                print("After logging in, press Enter here to continue...")
                input()
            except:
                print("✅ Already logged in or no login required")

            time.sleep(3)

            # Find text input area
            text_area = None
            selectors_to_try = [
                "textarea[placeholder*='Message']",
                "textarea",
                "[contenteditable='true']",
                "#prompt-textarea",
            ]

            for selector in selectors_to_try:
                try:
                    text_area = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"✅ Found text input: {selector}")
                    break
                except:
                    continue

            if not text_area:
                print("❌ Could not find text input area")
                return None

            # Prepare and send prompt
            prompt = _get_summary_prompt(transcript, max_length=3000)
            print("⌨️  Typing prompt...")
            text_area.clear()
            text_area.send_keys(prompt)

            # Find and click send button
            send_selectors = [
                "[data-testid='send-button']",
                "button[type='submit']",
                "button svg[class*='send']",
                "button:has(svg)",
            ]

            sent = False
            for selector in send_selectors:
                try:
                    send_button = driver.find_element(By.CSS_SELECTOR, selector)
                    if send_button.is_enabled():
                        send_button.click()
                        sent = True
                        print("✅ Message sent!")
                        break
                except:
                    continue

            if not sent:
                print("❌ Could not find send button. Please send manually.")
                print("Press Enter after ChatGPT responds...")
                input()
            else:
                print("⏳ Waiting for ChatGPT response...")
                time.sleep(Config.SELENIUM_WAIT_TIME)

            # Try to extract response
            response_selectors = [
                "[data-message-author-role='assistant']",
                ".markdown",
                "[class*='message']",
                "[class*='response']",
            ]

            for selector in response_selectors:
                try:
                    response_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if response_elements:
                        response_text = response_elements[-1].text
                        if response_text and len(response_text) > 50:
                            print(f"✅ Extracted response using: {selector}")
                            return response_text
                except:
                    continue

            # Manual fallback
            print("❌ Could not automatically extract response.")
            print("Please copy the ChatGPT response and paste it here:")
            response_text = input()
            return response_text if response_text.strip() else None

        finally:
            driver.quit()

    except ImportError:
        print(
            "❌ Selenium not installed. Install with: pip install selenium webdriver-manager"
        )
        return None
    except Exception as e:
        print(f"❌ ChatGPT web automation error: {e}")
        return None


def _create_simple_summary(transcript, max_sentences=4):
    """Create a simple rule-based extractive summary focused on meditation"""
    try:
        # Extract meditation content first
        meditation_content = _extract_meditation_content(transcript)

        # Split into sentences
        sentences = re.split(r"[.!?]+", meditation_content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        # Score sentences based on meditation/spiritual keywords
        meditation_keywords = [
            "mystery",
            "contemplate",
            "meditate",
            "reflect",
            "prayer",
            "god",
            "jesus",
            "mary",
            "rosary",
            "faith",
            "holy",
            "blessed",
            "scripture",
            "gospel",
            "christ",
            "lord",
            "divine",
            "grace",
            "salvation",
            "redemption",
            "incarnation",
            "resurrection",
        ]

        scored_sentences = []
        for i, sentence in enumerate(sentences):
            # Keyword score
            keyword_score = sum(
                1
                for keyword in meditation_keywords
                if keyword.lower() in sentence.lower()
            )

            # Avoid sentences that sound like intros
            intro_penalties = ["welcome", "hello", "today we begin", "i am", "this is"]
            penalty = sum(
                2 for phrase in intro_penalties if phrase.lower() in sentence.lower()
            )

            # Length score (prefer medium-length sentences)
            length_score = 1 if 30 <= len(sentence) <= 150 else 0

            total_score = keyword_score + length_score - penalty
            scored_sentences.append((sentence, total_score))

        # Sort by score and take top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)

        # Ensure we have at least 3 bullet points
        num_points = max(3, min(max_sentences, len(scored_sentences)))
        top_sentences = [s[0] for s in scored_sentences[:num_points]]

        # Format as bullet points
        bullet_points = []
        for sentence in top_sentences:
            # Clean up the sentence
            sentence = sentence.strip()
            if not sentence.endswith("."):
                sentence += "."
            bullet_points.append(f"• {sentence}")

        # Create markdown summary with bullet points
        bullet_text = "\n".join(bullet_points)

        return f"""**🙏 Meditation Summary**

{bullet_text}

*Simple extraction focusing on spiritual content*"""

    except Exception as e:
        print(f"❌ Error creating simple summary: {e}")
        # Fallback with basic bullet points
        meditation_content = _extract_meditation_content(transcript)
        preview = (
            meditation_content[:300] + "..."
            if len(meditation_content) > 300
            else meditation_content
        )

        return f"""**🙏 Meditation Summary**

• Today's meditation content extracted from the homily
• Focus on spiritual teachings and practical applications  
• Full transcript available for detailed review

*Content preview: {preview}*"""
