import os
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# Store search results for each user
pending_choices = {}


def search_movies(query):
    response = requests.get(
        "https://www.omdbapi.com/",
        params={
            "apikey": OMDB_API_KEY,
            "s": query
        },
        timeout=20
    )
    return response.json()


def get_movie_details(imdb_id):
    response = requests.get(
        "https://www.omdbapi.com/",
        params={
            "apikey": OMDB_API_KEY,
            "i": imdb_id,
            "plot": "short"
        },
        timeout=20
    )
    return response.json()


def get_rotten_tomatoes_rating(data):
    for rating in data.get("Ratings", []):
        if rating.get("Source") == "Rotten Tomatoes":
            return rating.get("Value")
    return "N/A"


def classify_movie(imdb_rating):
    try:
        rating = float(imdb_rating)
    except:
        rating = 0.0

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
    genre = data.get("Genre", "N/A")
    runtime = data.get("Runtime", "N/A")
    director = data.get("Director", "N/A")
    awards = data.get("Awards", "N/A")
    plot = data.get("Plot", "N/A")

    verdict = classify_movie(imdb_rating)

    return f"""
🎬 {title} ({year})

⭐ IMDb Rating: {imdb_rating}/10
🍅 Rotten Tomatoes: {rotten}
👥 IMDb Votes: {imdb_votes}

💰 Budget: N/A
💵 Box Office: {box_office}

🎭 Genre: {genre}
⏱ Runtime: {runtime}
🎬 Director: {director}
🏆 Awards: {awards}

📈 Verdict: {verdict}

📝 Plot:
{plot}
""".strip()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Welcome to the IMDb Movie Bot!\n\n"
        "Send any movie name.\n\n"
        "Examples:\n"
        "• Avatar\n"
        "• Interstellar\n"
        "• The Batman"
    )


async def movie_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # If user is choosing from previous results
    if user_id in pending_choices and text.isdigit():
        choice = int(text)
        movies = pending_choices[user_id]

        if 1 <= choice <= len(movies):
            imdb_id = movies[choice - 1]["imdbID"]

            await update.message.reply_text("🔍 Fetching details...")

            data = get_movie_details(imdb_id)

            if data.get("Response") == "False":
                await update.message.reply_text("❌ Movie not found.")
            else:
                await update.message.reply_text(format_movie(data))

            del pending_choices[user_id]
            return
        else:
            await update.message.reply_text("Please choose a valid number.")
            return

    # Search movies
    await update.message.reply_text("🔍 Searching...")

    data = search_movies(text)

    if data.get("Response") == "False":
        await update.message.reply_text(
            f"❌ {data.get('Error', 'Movie not found.')}"
        )
        return

    movies = data.get("Search", [])

    # Only one result → show directly
    if len(movies) == 1:
        imdb_id = movies[0]["imdbID"]
        details = get_movie_details(imdb_id)
        await update.message.reply_text(format_movie(details))
        return

    # Multiple results → ask user to choose
    pending_choices[user_id] = movies[:10]

    message = "🎬 Multiple movies found:\n\n"

    for i, movie in enumerate(pending_choices[user_id], start=1):
        message += f"{i}. {movie['Title']} ({movie['Year']})\n"

    message += "\nReply with the number of the movie you want."

    await update.message.reply_text(message)


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing.")
    if not OMDB_API_KEY:
        raise ValueError("OMDB_API_KEY is missing.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, movie_lookup)
    )

    print("IMDb Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
