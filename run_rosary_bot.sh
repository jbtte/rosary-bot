
# Rosary Bot Cron Wrapper Script

# Set the script directory (adjust path as needed)
SCRIPT_DIR="/Users/joaopaulo/code/jbtte/RIY"
LOG_FILE="$SCRIPT_DIR/logs/rosary_bot.log"

# Use the system Python3 (since dotenv was found)
PYTHON_PATH="/Library/Frameworks/Python.framework/Versions/3.11/bin/python3"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Add timestamp to log
echo "===========================================" >> "$LOG_FILE"
echo "$(date): Starting Rosary Bot" >> "$LOG_FILE"

# Change to script directory
cd "$SCRIPT_DIR"

# Run the bot and capture output
$PYTHON_PATH main.py >> "$LOG_FILE" 2>&1

# Check exit status
if [ $? -eq 0 ]; then
    echo "$(date): Rosary Bot completed successfully" >> "$LOG_FILE"
else
    echo "$(date): Rosary Bot failed with exit code $?" >> "$LOG_FILE"
fi

echo "===========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"