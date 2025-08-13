# Telegram Warning & Mute Bot
This is a Telegram bot that helps group admins automatically detect forbidden words in messages, warn users, and mute them if they exceed a set number of warnings.
Main features:

* Detects forbidden words and gives warnings
* Mutes a user for a set period (default: 10 minutes) after reaching the warning limit (default: 3)
* Stores and displays a warning history for each group
* Allows admins to manually reset warnings
* Automatically clears all warnings every 24 hours
* Resets a user’s warnings immediately after they are muted

---

## Requirements

* **Python** 3.9+
* **python-telegram-bot** >= 20.0

---

## Installation

1. **Clone the repository** or download the project files

2. **Install dependencies**:

   ```bash
   pip install python-telegram-bot==20.0
   ```

3. **Create the forbidden words list**:

   * Make a file named `words.txt` in the project folder.
   * Add each forbidden word or phrase on a new line, e.g.:

     ```
     badword1
     badword2
     ```

4. **Set your bot token**:

   * Get your token from [BotFather](https://t.me/BotFather).
   * Replace the `TOKEN` value in `robot.py` with your token.

---

## How to Use

1. **Run the bot**:

   ```bash
   python rob.py
   ```

2. **Add the bot to your group**:

   * Make the bot an **Admin**.
   * Enable **Restrict Members** permission.

3. **Available commands**:

   * `/history` → Show the last 10 warnings in the group.
   * `/reset <username or user_id>` → Reset warnings for a specific user (admin only).

4. **Automatic actions**:

   * Gives warnings when forbidden words are detected.
   * Mutes a user after reaching the warning limit and resets their warnings immediately.
   * Clears all warnings every 24 hours automatically.

---

## Files

* **robot.py** → Main bot script
* **words.txt** → Forbidden words list
* **group\_data.json** → Stores warnings & history

