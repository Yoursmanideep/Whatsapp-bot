import os
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIG
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")


# =========================
# HELPERS
# =========================
def get_movie_data(movie_name):
    url = "https://www.omdbapi.com/"
    params = {
        "apikey": OMDB_API_KEY,
        "t": movie_name,
        "plot": "short"
    }

    response = requests.get(url, params=params, timeout=20)
    data = response.json()

    if data.get("Response") == "False":
        return None

    return data


def get_rotten_tomatoes_rating(data):
    ratings = data.get("Ratings", [])
    for rating in ratings:
        if rating.get("Source") == "Rotten Tomatoes":
            return rating.get("Value")
    return "N/A"


def parse_money(value):
    """
    Converts strings like '$2,923,706,026' to integer.
    Returns None if unavailable.
    """
    if not value or value in ["N/A", ""]:
        return None

    try:
        cleaned = value.replace("$", "").replace(",", "")
        return int(cleaned)
    except:
        return None


def classify_movie(imdb_rating, box_office):
    """
    Simple conclusion logic.
    """
    try:
        rating = float(imdb_rating)
    except:
        rating = 0.0

    gross = parse_money(box_office)

    if rating >= 8.0:
        return "🔥 Hit"
    elif rating >= 7.0:
        return "👍 Average"
    elif rating >= 6.0:
        return "😐 Mixed"
    else:
        return "👎 Flop"


def format_movie(data):
    title = data.get("Title", "N/A")
    year = data.get("Year", "N/A")
    imdb_rating = data.get("imdbRating", "N/A")
    imdb_votes = data.get("imdbVotes", "N/A")
    rotten = get_rotten_tomatoes_rating(data)
    box_office = data.get("BoxOffice", "N/A")
    awards = data.get("Awards", "N/A")
    runtime = data.get("Runtime", "N/A")
    genre = data.get("Genre", "N/A")
    director = data.get("Director", "N/A")
    plot = data.get("Plot", "N/A")

    # OMDb usually does not provide budget
    budget = "N/A"

    conclusion = classify_movie(imdb_rating, box_office)

    return f"""
🎬 {title} ({year})

⭐ IMDb Rating: {imdb_rating}/10
🍅 Rotten Tomatoes: {rotten}
👥 IMDb Votes: {imdb_votes}

💰 Budget: {budget}
💵 Box Office: {box_office}

🎭 Genre: {genre}
⏱ Runtime: {runtime}
🎬 Director: {director}
🏆 Awards: {awards}

📈 Verdict: {conclusion}

📝 Plot:
{plot}
""".strip()


# =========================
# TELEGRAM HANDLERS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Welcome to the IMDb Movie Bot!\n\n"
        "Just send me any movie name.\n\n"
        "Examples:\n"
        "• Interstellar\n"
        "• Avatar\n"
        "• Pushpa\n"
        "• The Dark Knight"
    )


async def movie_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    movie_name = update.message.text.strip()

    if not movie_name:
        await update.message.reply_text("Please send a movie name.")
        return

    await update.message.reply_text("🔍 Searching...")

    try:
        data = get_movie_data(movie_name)

        if not data:
            await update.message.reply_text(
                "❌ Movie not found.\nTry another title."
            )
            return

        result = format_movie(data)
        await update.message.reply_text(result)

    except Exception as e:
        print("ERROR:", e)
        await update.message.reply_text(
            "⚠️ Something went wrong. Please try again."
        )


# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, movie_lookup)
    )

    print("IMDb Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
