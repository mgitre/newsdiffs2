# newsdiffs2
A project based on [ecprice's newsdiffs](https://github.com/ecprice/newsdiffs).

Running `scraper.py` scrapes articles from NYTimes, WaPo, and APNews. I recommend attaching it to a cronjob.

`server.py` serves the web frontend, letting you view articles.

Articles that haven't changed in 2 days but have changes on record are saved to `archive.json`.
