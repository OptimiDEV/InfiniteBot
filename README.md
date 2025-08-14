# Civita

A feature-rich Discord bot built with [Disnake](https://docs.disnake.dev/), designed for community moderation, YouTube monitoring, AI-generated content, and interaction automation.

---

## Features

- 👋 Welcomes new members and announces when someone leaves.
- 🧠 Posts a **daily "Question of the Day"** from **Google Gemini** at midnight.
- ⚠️ Lets users **report messages** using reaction emojis:
  - 🏴 for rule-breaking
  - 🔨 for racism/homophobia
- 🔒 Automoderation powered by `better-profanity` to delete offensive messages.
- ⚙️ Includes a slash command to force-post the QOTD at any time.
- Allows you to ask the bot everything you want by mentioning it

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/OptimiDEV/Civita.git
cd Civita
````

### 2. Create a virtual environment (optional but recommended)

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

If you don't have `requirements.txt`, install manually:

```bash
pip install disnake sqlite3 google google-genai requests better-profanity
```

---

## Configuration

In your `bot.py`, replace the following:

```python
TOKEN = "YOUR_DISCORD_BOT_TOKEN"
GEMINI_API_KEY = "YOUR_GOOGLE_GEMINI_API_KEY"
```

You can get a Google Gemini API key at: [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)

---

## Commands
Moved to https://optimidev.github.io/Civita/docs/

---

## Message Reporting

Users can react to any message with:

* 🏴 → Report general rule-breaking
* 🔨 → Report racism or homophobia

These reports will be logged in the designated moderation channel.

---

## AI Integration (Gemini)

Questions of the Day are generated using [Google Gemini](https://ai.google.dev/). The bot queries Gemini every day at **00:00 UTC** server time and sends the question to your configured channel.

---

## Auto Moderation

Offensive messages (based on the built-in word list from `better-profanity`) are automatically deleted and logged.

---

## 📦 Example `.env` (optional)

You can use `.env` to store secrets securely if you modify the bot to load from it:

```
DISCORD_TOKEN=your_bot_token
GEMINI_API_KEY=your_gemini_api_key
```

---

## 📝 License

MIT License. Use freely with attribution.

---

## 💡 Credits

* Built with [Disnake](https://github.com/DisnakeDev/disnake)
* AI integration via [Google Generative AI](https://ai.google.dev/)
* Profanity filtering via [better-profanity](https://github.com/snguyenthanh/better-profanity)



Just say the word!
```
