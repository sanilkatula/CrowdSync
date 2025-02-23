import twitchio
from twitchio.ext import commands
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import time
import collections

# Twitch credentials
TWITCH_NICKNAME = "Crowdsync"
TWITCH_TOKEN = "oauth:qz24c4g5i57ixlr0h9yg2kf19e61nt"

# Sentiment analysis setup
analyzer = SentimentIntensityAnalyzer()

# Track recent sentiment scores for overall room vibe
recent_sentiments = collections.deque(maxlen=20)  # Stores last 20 messages for rolling average
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
        return "⚪ Waiting for messages..."  # No chat data yet
    
    avg_sentiment = sum(recent_sentiments) / len(recent_sentiments)
    mood = get_mood(avg_sentiment)
    
    if avg_sentiment == 0:
        return "⚪ Neutral - Chat seems quiet or indifferent."
    elif -0.1 < avg_sentiment < 0.1:
        return "😐 Neutral but slightly shifting - Chat is on the edge of emotion."
    elif avg_sentiment > 0 and len([s for s in recent_sentiments if s > 0.5]) > len(recent_sentiments) / 2:
        return "🎉 Mostly positive - More than half of the chat is feeling good!"
    elif avg_sentiment < 0 and len([s for s in recent_sentiments if s < -0.5]) > len(recent_sentiments) / 2:
        return "⚠️ Mostly negative - There's a lot of frustration in the chat."
    
    return mood

class TwitchBot(commands.Bot):
    def __init__(self, channel_name):
        super().__init__(token=TWITCH_TOKEN, prefix="!", initial_channels=[channel_name])
        self.current_channel = channel_name

    async def event_ready(self):
        print(f"✅ Bot connected as {self.nick}")

    async def event_message(self, message):
        global last_update_time

        if message.echo:
            return

        sentiment_score = analyzer.polarity_scores(message.content)["compound"]
        mood = get_mood(sentiment_score)
        
        # Store sentiment score for overall room vibe calculation
        recent_sentiments.append(sentiment_score)

        # Print individual message vibe
        print(f"[{message.author.name}]: {message.content} ({mood}, Score: {sentiment_score})")

        # Update room vibe every 10 seconds
        if time.time() - last_update_time > 10:
            overall_vibe = get_overall_vibe()
            print(f"\n🌡️ **Overall Room Vibe:** {overall_vibe} (Based on last {len(recent_sentiments)} messages)\n")
            last_update_time = time.time()

    @commands.command(name="setchannel")
    async def set_channel(self, ctx: commands.Context, channel_name: str):
        """Allows user to change the monitored Twitch channel."""
        self.current_channel = channel_name
        await self.join_channels([channel_name])
        await ctx.send(f"✅ Now monitoring {channel_name} for vibe analysis!")
        print(f"🔄 Switched to monitoring {channel_name}")

if __name__ == "__main__":
    channel = input("Enter the Twitch channel you want to monitor: ")
    bot = TwitchBot(channel)
    bot.run()