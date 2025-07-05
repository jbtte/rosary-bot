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
            print(f"✂️  Found '{primary_marker}' at position {pos}")
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

Format requirements:
* First bullet: If an artwork/painting and artist are mentioned, include that (e.g., "Artwork: The Annunciation by Fra Angelico"). If no artwork mentioned, skip this bullet.
* Next 8 bullets: Key spiritual insights from the meditation (each bullet up to 150 characters)
* Focus on the main spiritual teachings and practical applications

Structure:
* Start with artwork info (if mentioned)
* Provide 8 bullet points with key insights
* End with a practical reflection in italics

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

    # Try ChatGPT web automation as fallback
    summary = _try_chatgpt_web(transcript)
    if summary:
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

        # Enhanced Chrome options for stability
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--memory-pressure-off")
        chrome_options.add_argument("--max_old_space_size=4096")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # Additional stability options
        chrome_options.add_argument("--remote-debugging-port=0")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")

        print("Setting up ChromeDriver...")

        # Use webdriver-manager with explicit version handling
        try:
            service = Service(ChromeDriverManager().install())
        except Exception as e:
            print(f"ChromeDriverManager failed: {e}")
            # Try manual path
            service = Service("/opt/homebrew/bin/chromedriver")

        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Set timeouts
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)

        # Execute script to hide webdriver property
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        try:
            print("Opening ChatGPT...")
            driver.get("https://chat.openai.com")
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

            # Re-enable JavaScript if needed
            driver.execute_script("console.log('JavaScript enabled for interaction')")

            # Find text input area with Portuguese interface support
            text_area = None
            selectors_to_try = [
                "textarea[placeholder*='Mensagem']",  # Portuguese "Message"
                "textarea[placeholder*='Digite']",  # Portuguese "Type"
                "textarea[placeholder*='Escreva']",  # Portuguese "Write"
                "textarea[placeholder*='Message']",  # English fallback
                "textarea[data-id='root']",
                "div[contenteditable='true']",
                "textarea",
                "#prompt-textarea",
                "[role='textbox']",
            ]

            for selector in selectors_to_try:
                try:
                    print(f"Trying text input selector: {selector}")
                    text_area = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"✅ Found text input: {selector}")
                    break
                except Exception as e:
                    print(f"Failed with {selector}: {e}")
                    continue

            if not text_area:
                print("❌ Could not find text input area")
                # Take screenshot for debugging
                try:
                    driver.save_screenshot("/tmp/chatgpt_debug.png")
                    print("📸 Screenshot saved to /tmp/chatgpt_debug.png")

                    # Print page source snippet for debugging
                    page_source = driver.page_source
                    if "textarea" in page_source.lower():
                        print("📝 Found textarea elements in page")
                    if "contenteditable" in page_source.lower():
                        print("📝 Found contenteditable elements in page")

                except Exception as debug_e:
                    print(f"Debug screenshot failed: {debug_e}")
                return None

            # Prepare and send prompt
            prompt = _get_summary_prompt(transcript, max_length=3000)
            print("⌨️  Typing prompt...")

            # Clear and type with multiple methods
            try:
                # Method 1: Standard Selenium
                text_area.clear()
                text_area.send_keys(prompt)
                print("✅ Used standard Selenium input")
            except Exception as e1:
                print(f"Standard input failed: {e1}")
                try:
                    # Method 2: JavaScript input
                    driver.execute_script("arguments[0].value = '';", text_area)
                    driver.execute_script(
                        "arguments[0].value = arguments[1];", text_area, prompt
                    )
                    print("✅ Used JavaScript input")
                except Exception as e2:
                    print(f"JavaScript input failed: {e2}")
                    try:
                        # Method 3: Focus and type
                        driver.execute_script("arguments[0].focus();", text_area)
                        text_area.send_keys(prompt)
                        print("✅ Used focus and type")
                    except Exception as e3:
                        print(f"All input methods failed: {e3}")
                        print("❌ Could not enter text. Please type manually.")
                        print("Press Enter here after typing the prompt...")
                        input()

            # Find and click send button (Portuguese interface)
            send_selectors = [
                "button[aria-label*='Enviar']",  # Portuguese "Send"
                "button[aria-label*='buscar']",  # Portuguese "Search"
                "[data-testid='send-button']",  # Standard data attribute
                "button[aria-label*='Send']",  # English fallback
                "button[type='submit']",  # Generic submit button
                "button:has(svg)",  # Button with icon
                ".btn-primary",  # CSS class fallback
            ]

            sent = False
            for selector in send_selectors:
                try:
                    print(f"Trying send button selector: {selector}")
                    send_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )

                    # Try both regular click and JavaScript click
                    try:
                        send_button.click()
                    except:
                        driver.execute_script("arguments[0].click();", send_button)

                    sent = True
                    print(f"✅ Message sent using: {selector}")
                    break
                except Exception as e:
                    print(f"Failed with {selector}: {e}")
                    continue

            # Additional Portuguese-specific attempts with XPath
            if not sent:
                try:
                    print("Trying Portuguese XPath selectors...")
                    portuguese_selectors = [
                        "//button[contains(text(), 'Enviar')]",
                        "//button[contains(text(), 'buscar')]",
                        "//button[contains(@aria-label, 'Enviar')]",
                        "//button[contains(@aria-label, 'buscar')]",
                        "//input[@type='submit']",
                        "//button[contains(@class, 'send')]",
                    ]

                    for xpath in portuguese_selectors:
                        try:
                            print(f"Trying XPath: {xpath}")
                            send_button = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, xpath))
                            )
                            driver.execute_script("arguments[0].click();", send_button)
                            sent = True
                            print(f"✅ Message sent using XPath: {xpath}")
                            break
                        except Exception as e:
                            print(f"XPath failed {xpath}: {e}")
                            continue
                except Exception as e:
                    print(f"Portuguese selectors failed: {e}")

            # Last resort: Press Enter key
            if not sent:
                print("❌ Could not find send button. Trying Enter key...")
                try:
                    text_area.send_keys("\n")
                    sent = True
                    print("✅ Used Enter key to send")
                except Exception as e:
                    print(f"Enter key failed: {e}")
                    print("❌ All send methods failed. Please send manually.")
                    print("Press Enter here after you manually click send...")
                    input()

            if sent:
                print("⏳ Waiting for ChatGPT response...")
                time.sleep(20)  # Give more time for response

            # Try to extract response with Portuguese interface support
            response_selectors = [
                "[data-message-author-role='assistant']",
                "[data-testid*='conversation-turn']",
                ".markdown",
                ".prose",
                "[class*='message']",
                "[class*='resposta']",  # Portuguese "response"
                "[class*='assistant']",
                "[class*='bot']",
                "div[role='presentation']",
                ".whitespace-pre-wrap",
            ]

            response_text = None
            for selector in response_selectors:
                try:
                    print(f"Trying response selector: {selector}")
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    response_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if response_elements:
                        # Try each element to find the one with substantial content
                        for element in response_elements:
                            element_text = element.text.strip()
                            if (
                                len(element_text) > 50
                                and "bullet" in element_text.lower()
                            ):
                                response_text = element_text
                                print(f"✅ Extracted response using: {selector}")
                                print(f"Response preview: {element_text[:100]}...")
                                break
                        if response_text:
                            break
                except Exception as e:
                    print(f"Selector {selector} failed: {e}")
                    continue

            # Additional Portuguese-specific response extraction
            if not response_text:
                try:
                    print("Trying Portuguese-specific response extraction...")
                    # Look for any div containing bullet points or meditation content
                    xpath_selectors = [
                        "//div[contains(text(), '•')]",
                        "//div[contains(text(), 'meditação')]",  # Portuguese "meditation"
                        "//div[contains(text(), 'oração')]",  # Portuguese "prayer"
                        "//div[contains(text(), 'reflexão')]",  # Portuguese "reflection"
                        "//div[contains(text(), 'Artwork')]",
                        "//div[contains(text(), 'Maria')]",  # Portuguese "Mary"
                        "//div[contains(text(), 'Jesus')]",
                    ]

                    for xpath in xpath_selectors:
                        try:
                            elements = driver.find_elements(By.XPATH, xpath)
                            for element in elements:
                                element_text = element.text.strip()
                                if len(element_text) > 100:  # Substantial content
                                    response_text = element_text
                                    print(f"✅ Extracted via XPath: {xpath}")
                                    break
                            if response_text:
                                break
                        except:
                            continue
                except Exception as e:
                    print(f"Portuguese extraction failed: {e}")

            # Manual fallback with better instructions
            if not response_text:
                print("❌ Could not automatically extract response.")
                print("📋 Please copy the ENTIRE ChatGPT response and paste it here.")
                print(
                    "💡 Make sure to copy all bullet points and the complete summary."
                )
                print("📝 Paste the response below:")
                response_text = input().strip()

                if not response_text:
                    print("❌ No response provided")
                    return None
                elif len(response_text) < 50:
                    print(
                        "⚠️  Response seems too short. Are you sure you copied everything?"
                    )
                    print(
                        "📝 Try again (or press Enter to continue with short response):"
                    )
                    retry_response = input().strip()
                    if retry_response:
                        response_text = retry_response

            return response_text if response_text else None

        finally:
            print("Closing browser...")
            driver.quit()

    except ImportError:
        print(
            "❌ Selenium not installed. Install with: pip install selenium webdriver-manager"
        )
        return None
    except Exception as e:
        print(f"❌ ChatGPT web automation error: {e}")
        import traceback

        traceback.print_exc()
        return None


def _create_simple_summary(transcript, max_sentences=8):
    """Create a simple rule-based extractive summary focused on meditation"""
    try:
        # Extract meditation content first
        meditation_content = _extract_meditation_content(transcript)

        # Look for artwork mentions
        artwork_info = _extract_artwork_info(meditation_content)

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
                1 for phrase in intro_penalties if phrase.lower() in sentence.lower()
            )

            # Prefer sentences up to 150 characters
            length_score = (
                2 if 30 <= len(sentence) <= 150 else 1 if len(sentence) <= 200 else 0
            )

            total_score = keyword_score + length_score - penalty
            scored_sentences.append((sentence, total_score))

        # Sort by score and take top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)

        # Create bullet points
        bullet_points = []

        # Add artwork info if found
        if artwork_info:
            bullet_points.append(f"• {artwork_info}")

        # Add spiritual insights (8 total, or 7 if artwork was added)
        remaining_bullets = 8 if not artwork_info else 7
        top_sentences = [s[0] for s in scored_sentences[:remaining_bullets]]

        for sentence in top_sentences:
            sentence = sentence.strip()

            # Trim if over 150 characters
            if len(sentence) > 150:
                sentence = sentence[:147] + "..."

            if not sentence.endswith(".") and not sentence.endswith("..."):
                sentence += "."
            bullet_points.append(f"• {sentence}")

        # Ensure we have at least 6 bullet points total
        while len(bullet_points) < 6:
            bullet_points.append("• Trust in God's providence and Mary's intercession.")

        # Create markdown summary with bullet points
        bullet_text = "\n".join(bullet_points)

        return f"""**🙏 Meditation Summary**

{bullet_text}

*Simple summary for hand copying and reflection*"""

    except Exception as e:
        print(f"❌ Error creating simple summary: {e}")
        # Fallback with basic bullet points
        return f"""**🙏 Meditation Summary**

• Today's meditation focuses on spiritual growth and devotion
• Trust in God's plan and follow Mary's example of faith
• Pray the rosary with contemplation of the mysteries
• Seek God's grace in daily challenges and decisions
• Practice humility and service to others in need
• Find peace through prayer and trust in divine providence

*Simple meditation summary for reflection*"""
