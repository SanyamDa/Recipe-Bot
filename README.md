# 🥘 Recipe Bot

> **Telegram bot** that whips up personalised recipes on demand  
> *Python 3 · python-telegram-bot v20 · SQLite3 · OpenAI GPT-4*

![demo GIF](docs/demo.gif)

---

## ✨ Features

| Capability | What it does |
|-------------|-------------|
| **Interactive onboarding** | `/onboard` collects dietary restrictions, skill level & budget—can be changed any time. |
| **Guided recipe builder** | `/recipe` asks cuisine → meal type → servings → time → ingredients, then returns a full recipe: ingredients, steps, nutrition, cost. |
| **Pantry assumptions** | Salt, oil, etc., plus common flavour bases for each cuisine are auto-assumed so users list only unique ingredients. |
| **⭐ Favorites** | Inline “Add to favorites” button; `/favorites` lists titles; `/specific <name>` shows the full recipe. |
| **Audit log** | Every request & recipe saved in SQLite for analytics or retraining prompts. |

---

## 🚀 Quick Start

```bash
git clone https://github.com/your-handle/recipe-bot.git
cd recipe-bot
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 1  environment vars
cp .env.example .env            # fill TELEGRAM_TOKEN & OPENAI_API_KEY

# 2  initialise database
python -c "from database.db import init_db; init_db()"

# 3  run the bot (long-polling)
python bot.py
