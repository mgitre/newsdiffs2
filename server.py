# -*- coding: utf-8 -*-
"""
Created on Fri Sep 11 10:15:47 2020

@author: Max
"""

from flask import Flask, render_template, abort, redirect
from scraper import WashingtonPost, NewYorkTimes, APNews
import json, re
import yaml
import postgres_handler

app = Flask(__name__)
app.config["DEBUG"] = True
nameToClass = {"washingtonpost":WashingtonPost, "nytimes":NewYorkTimes, "apnews":APNews}

with open("config.yaml") as f:
    config=yaml.safe_load(f)['SERVER']

base_url=config['ACCESS']
host=config['HOST']
port=config['PORT']


def fixUrl(c, url):
    newsclass = c()
    step1 = re.search(newsclass.regex, url)
    if step1 == None:
        return
    step2 = newsclass.formatUrl(step1.group(0))
    return step2

@app.route('/<site>/<path:article>')
def articleView(site, article):
    if not site in nameToClass:
        abort(404)
    fixedUrl = fixUrl(nameToClass[site], article)
    if fixedUrl==None:
        abort(404)
    if fixedUrl != article:
        return redirect(base_url+"{}/{}".format(site,fixedUrl))
    article_handler=postgres_handler.ArticleHandler(article)
    if not article_handler.exists:
        abort(404)
    articledata = article_handler.databaseEntry[1]
    return render_template("article.html", articledata=articledata)


app.run(port=port, host=host)
