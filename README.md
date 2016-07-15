About
=====

When my notes get large, I like to break them out and create index/table-of-contents notes. However, it is hard to say later when looking on such note whether it belongs to any index.

This project can help you with that. It takes notes from looking like that:

<img src="https://cloud.githubusercontent.com/assets/1933752/16887746/7ec44268-4ae4-11e6-9ea8-44bee18889de.png" height="300px">

Then the utility goes over all your recently edited notes and adds backlinks to the content notes, back to the notes that link to it. Bringing it to look like this:

<img src="https://cloud.githubusercontent.com/assets/1933752/16868422/32b3f8c8-4a80-11e6-9db7-bc9c649c9fb9.png" height="300px">


Setup
=====

* Run via Python 2.7
* Get the code: `git clone` or download as ZIP and extract
* Run in the folder: `pip install -r requirements.txt`
* Generate developers token [here](https://www.evernote.com/api/DeveloperToken.action)
* Create a new file in project root named `local_settings.py` and write your token in it like so: 

`token = "YOUR_TOKEN_GOES HERE"`

* Run: `python main.py`
* Tip: Schedule the execution to run daily via a scheduler

Usage
=====

Just run: `python main.py`

Automatically runs since the last time it was executed. If it was never executed, processes notes from last 3 months.
