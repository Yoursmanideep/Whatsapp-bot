# Store pending choices for each user
pending_choices = {}

async def movie_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # =========================
    # USER SELECTS FROM LIST
    # =========================
    if user_id in pending_choices and text.isdigit():
        choice = int(text)

        movies = pending_choices[user_id]

        if 1 <= choice <= len(movies):
            selected = movies[choice - 1]
            imdb_id = selected["imdbID"]

            await update.message.reply_text("🔍 Fetching details...")

            try:
                url = "https://www.omdbapi.com/"
                params = {
                    "apikey": OMDB_API_KEY,
                    "i": imdb_id,
                    "plot": "short"
                }

                response = requests.get(url, params=params, timeout=20)
                data = response.json()

                if data.get("Response") == "False":
                    await update.message.reply_text("❌ Movie not found.")
                else:
                    await update.message.reply_text(format_movie(data))

            except Exception as e:
                print("ERROR:", e)
                await update.message.reply_text("⚠️ Something went wrong.")

            # Clear stored choices
            del pending_choices[user_id]
            return
        else:
            await update.message.reply_text("Please choose a valid number.")
            return

    # =========================
    # SEARCH FOR MOVIES
    # =========================
    await update.message.reply_text("🔍 Searching...")

    try:
        url = "https://www.omdbapi.com/"
        params = {
            "apikey": OMDB_API_KEY,
            "s": text
        }

        response = requests.get(url, params=params, timeout=20)
        data = response.json()

        print("SEARCH RESPONSE:", data)

        if data.get("Response") == "False":
            await update.message.reply_text(
                f"❌ {data.get('Error', 'Movie not found.')}"
            )
            return

        movies = data.get("Search", [])

        # If only one result, fetch full details directly
        if len(movies) == 1:
            imdb_id = movies[0]["imdbID"]

            detail_params = {
                "apikey": OMDB_API_KEY,
                "i": imdb_id,
                "plot": "short"
            }

            detail_response = requests.get(
                url,
                params=detail_params,
                timeout=20
            )

            detail_data = detail_response.json()
            await update.message.reply_text(format_movie(detail_data))
            return

        # Multiple matches → ask user to choose
        pending_choices[user_id] = movies[:10]

        message = "🎬 Multiple movies found:\n\n"

        for i, movie in enumerate(pending_choices[user_id], start=1):
            message += (
                f"{i}. {movie['Title']} ({movie['Year']})\n"
            )

        message += "\nReply with the number of the movie you want."

        await update.message.reply_text(message)

    except Exception as e:
        print("ERROR:", e)
        await update.message.reply_text(
            "⚠️ Something went wrong. Please try again."
        )
