import os
import twitchio
from twitchio.ext import commands
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import time
import collections
import asyncio
from flask import Flask, jsonify, request
import threading
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Twitch Token from Environment Variables
TWITCH_OAUTH_TOKEN = os.getenv("TWITCH_OAUTH_TOKEN")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

# Validate required secrets
if not TWITCH_OAUTH_TOKEN:
    raise ValueError("❌ TWITCH_OAUTH_TOKEN is missing. Set it in your .env or deployment environment.")

# Initialize Flask App
app = Flask(__name__)
CORS(app)
app.secret_key = FLASK_SECRET_KEY

# Global Variables
current_channel = None
bot = None  # Global bot instance
analyzer = SentimentIntensityAnalyzer()
recent_sentiments = collections.deque(maxlen=20)  # Rolling average of sentiments
recent_messages = collections.deque(maxlen=20)  # Store last 20 messages
last_update_time = time.time()

# Mood categories
def get_mood(sentiment_score):
    if sentiment_score >= 0.75:
        return "🚀 Hyped - The chat is full of excitement and energy!"
    elif sentiment_score >= 0.5:
        return "😃 Happy - The chat is generally positive and engaged."
    elif sentiment_score >= 0.05:
        return "🙂 Chill - Chat is relaxed, with a friendly vibe."
    elif sentiment_score > -0.05:
        return "😐 Neutral - No strong emotions, the chat is balanced."
    elif sentiment_score > -0.5:
        return "😡 Annoyed - Some users are showing frustration or negativity."
    else:
        return "🔥 Toxic - The chat has high levels of negativity or hostility."

# Calculate overall room vibe
def get_overall_vibe():
    if not recent_sentiments:
        return "⚪ Waiting for messages..."
    
    avg_sentiment = sum(recent_sentiments) / len(recent_sentiments)
    return get_mood(avg_sentiment)

class TwitchBot(commands.Bot):
    def __init__(self, channel_name):
        super().__init__(token=TWITCH_OAUTH_TOKEN, prefix="!", initial_channels=[channel_name])
        self.current_channel = channel_name

    async def event_ready(self):
        print(f"✅ Bot connected as {self.nick}")

    async def event_message(self, message):
        global last_update_time
        if message.echo:
            return

        sentiment_score = analyzer.polarity_scores(message.content)["compound"]
        mood = get_mood(sentiment_score)
        recent_sentiments.append(sentiment_score)
        recent_messages.append({"user": message.author.name, "content": message.content, "mood": mood})

        print(f"[{message.author.name}]: {message.content} ({mood}, Score: {sentiment_score})")

        if time.time() - last_update_time > 10:
            last_update_time = time.time()

    async def switch_channel(self, new_channel: str):
        await self.join_channels([new_channel])
        print(f"🔄 Switched to monitoring {new_channel}")

# 🔹 1️⃣ Set Channel API
@app.route("/setchannel", methods=["POST"])
def set_channel():
    global current_channel, bot
    data = request.get_json()
    new_channel = data.get("channel")

    if not new_channel:
        return jsonify({"error": "Channel name required"}), 400

    current_channel = new_channel

    if bot:
        loop = bot.loop
        future = asyncio.run_coroutine_threadsafe(bot.switch_channel(new_channel), loop)
        future.result()
        return jsonify({"message": f"Now monitoring {new_channel}"})
    else:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        bot = TwitchBot(new_channel)
        thread = threading.Thread(target=lambda: loop.run_until_complete(bot.start()), daemon=True)
        thread.start()
        return jsonify({"message": f"Bot started and monitoring {new_channel}"})


# 🔹 2️⃣ Get Vibe & Messages API
@app.route("/vibe", methods=["GET"])
def get_vibe():
    return jsonify({"vibe": get_overall_vibe(), "messages": list(recent_messages)})

# 🔹 3️⃣ Reset Monitoring API
@app.route("/reset", methods=["POST"])
def reset_bot():
    global bot, current_channel

    if bot:
        loop = bot.loop
        asyncio.run_coroutine_threadsafe(bot.close(), loop)

        bot = None
        current_channel = None

        return jsonify({"message": "Bot has been stopped. Ready for a new channel selection!"})
    
    return jsonify({"error": "No bot is running"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
