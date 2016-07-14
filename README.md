About
=====

Have you ever looked at a note and wondered: Does it belong to any topic? Is it linked from somewhere else?

This project can help you with that. It takes notes from looking like that:




Setup
=====

* Run via Python 2.7
* Get the code: `git clone` or download as ZIP and extract
* Run in the folder: `pip install -r requirements.txt`
* Generate developers token [here](https://www.evernote.com/api/DeveloperToken.action)
* Create a new file in project root named `local_settings.py` and write your token in it like so: `token = "YOUR_TOKEN_GOES HERE"`
* Run: `python main.py`
* Tip: Schedule the execution to run daily via a scheduler

Usage
=====

Just run: `python main.py`

Automatically runs since the last time it was executed. If it was never executed, processes notes from last 3 months.
