import os
import re
import requests
import urllib.parse

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ==========================================
# CONFIG
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# user_id -> list of search results
pending_choices = {}

# user_id -> selected movie data
selected_movies = {}


# ==========================================
# OMDB HELPERS
# ==========================================
def parse_title_and_year(text):
    """
    Supports:
    - Avengers
    - Avengers 2012
    - Batman 2022
    """
    text = text.strip()
    match = re.match(r"^(.*?)(?:\s+(\d{4}))?$", text)

    if match:
        title = match.group(1).strip()
        year = match.group(2)
        return title, year

    return text, None


def search_movies(query, year=None):
    params = {
        "apikey": OMDB_API_KEY,
        "s": query
    }

    if year:
        params["y"] = year

    response = requests.get(
        "https://www.omdbapi.com/",
        params=params,
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
# ==========================================
# PART 2 OF 3 — Buttons and Handlers
# ==========================================

def build_movie_buttons():
    keyboard = [
        [
            InlineKeyboardButton(
                "🎭 Show Cast",
                callback_data="show_cast"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def build_back_button():
    keyboard = [
        [
            InlineKeyboardButton(
                "🔙 Back to List",
                callback_data="back_to_list"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def build_cast_buttons(cast_names):
    """
    Creates clickable buttons that open Google Images
    for each actor.
    """
    keyboard = []

    for actor in cast_names[:10]:
        actor = actor.strip()
        if not actor:
            continue

        query = urllib.parse.quote_plus(actor)
        url = (
            "https://www.google.com/search"
            f"?tbm=isch&q={query}"
        )

        keyboard.append([
            InlineKeyboardButton(actor, url=url)
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 Back to Movie",
            callback_data="back_to_movie"
        )
    ])

    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Welcome to the IMDb Movie Bot!\n\n"
        "Send any movie name.\n\n"
        "Examples:\n"
        "• Avatar\n"
        "• Avengers 2012\n"
        "• Interstellar"
    )


async def send_movie(chat_id, context, data, user_id):
    """
    Sends poster + movie details + action buttons.
    """
    selected_movies[user_id] = data

    poster = data.get("Poster", "N/A")

    # Send poster if available
    if poster and poster != "N/A":
        try:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=poster
            )
        except Exception as e:
            print("Poster Error:", e)

    # Send movie details
    await context.bot.send_message(
        chat_id=chat_id,
        text=format_movie(data),
        reply_markup=build_movie_buttons()
    )


async def movie_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # ======================================
    # USER CHOOSES NUMBER FROM SEARCH LIST
    # ======================================
    if user_id in pending_choices and text.isdigit():
        choice = int(text)
        movies = pending_choices[user_id]

        if 1 <= choice <= len(movies):
            imdb_id = movies[choice - 1]["imdbID"]

            await update.message.reply_text(
                "🔍 Fetching details..."
            )

            data = get_movie_details(imdb_id)

            if data.get("Response") == "False":
                await update.message.reply_text(
                    "❌ Movie not found."
                )
            else:
                await send_movie(
                    update.effective_chat.id,
                    context,
                    data,
                    user_id
                )

            return
        else:
            await update.message.reply_text(
                "❌ Invalid choice.\n"
                "Use the button below to view the list again.",
                reply_markup=build_back_button()
            )
            return

    # ======================================
    # NEW SEARCH
    # ======================================
    title, year = parse_title_and_year(text)

    await update.message.reply_text("🔍 Searching...")

    data = search_movies(title, year)

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

        await send_movie(
            update.effective_chat.id,
            context,
            details,
            user_id
        )
        return

    # Multiple results → save list
    pending_choices[user_id] = movies[:10]

    message = "🎬 Multiple movies found:\n\n"

    for i, movie in enumerate(
        pending_choices[user_id],
        start=1
    ):
        message += (
            f"{i}. {movie['Title']} "
            f"({movie['Year']})\n"
        )

    message += "\nReply with the number of the movie you want."

    await update.message.reply_text(
        message,
        reply_markup=build_back_button()
    )

# ==========================================
# PART 3 OF 3 — Callback Buttons and Main
# ==========================================

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()

    # ======================================
    # SHOW CAST BUTTON
    # ======================================
    if query.data == "show_cast":
        if user_id not in selected_movies:
            await query.edit_message_text(
                "❌ No movie selected yet."
            )
            return

        data = selected_movies[user_id]
        cast_text = data.get("Actors", "N/A")

        if cast_text == "N/A":
            await query.edit_message_text(
                "❌ Cast information not available."
            )
            return

        cast_names = [name.strip() for name in cast_text.split(",")]

        await query.edit_message_text(
            "🎭 Cast Members\n\n"
            "Tap any actor name to open Google Images.",
            reply_markup=build_cast_buttons(cast_names)
        )
        return

    # ======================================
    # BACK TO MOVIE BUTTON
    # ======================================
    if query.data == "back_to_movie":
        if user_id not in selected_movies:
            await query.edit_message_text(
                "❌ No movie selected yet."
            )
            return

        data = selected_movies[user_id]

        await query.edit_message_text(
            format_movie(data),
            reply_markup=build_movie_buttons()
        )
        return

    # ======================================
    # BACK TO LIST BUTTON
    # ======================================
    if query.data == "back_to_list":
        if user_id not in pending_choices:
            await query.edit_message_text(
                "❌ No previous search list found."
            )
            return

        movies = pending_choices[user_id]

        message = "🎬 Multiple movies found:\n\n"

        for i, movie in enumerate(movies, start=1):
            message += (
                f"{i}. {movie['Title']} "
                f"({movie['Year']})\n"
            )

        message += "\nReply with the number of the movie you want."

        await query.edit_message_text(
            message,
            reply_markup=build_back_button()
        )
        return


def main():
    # Validate environment variables
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing.")
    if not OMDB_API_KEY:
        raise ValueError("OMDB_API_KEY is missing.")

    # Create Telegram application
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            movie_lookup
        )
    )

    print("IMDb Bot is running...")

    # Start polling
    app.run_polling()


if __name__ == "__main__":
    main()
