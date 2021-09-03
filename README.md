# newsdiffs2
A project based on [ecprice's newsdiffs](https://github.com/ecprice/newsdiffs).

Configure all settings in `config.yaml`.

Running `scraper.py` scrapes articles from NYTimes, Washington Post, and APNews. I recommend attaching it to a cronjob.

`server.py` serves the web frontend, letting you view articles.


### Database Setup

Import newsdiffs2.sql into PostgreSQL

Tested on PostgreSQL 12.8