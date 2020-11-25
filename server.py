# -*- coding: utf-8 -*-
"""
Created on Fri Sep 11 10:15:47 2020

@author: Max
"""

from flask import Flask, render_template, abort, redirect
from classbased import WashingtonPost, NewYorkTimes, APNews
import json, re
app = Flask(__name__)
app.config["DEBUG"] = True
nameToClass = {"washingtonpost":WashingtonPost, "nytimes":NewYorkTimes, "apnews":APNews}
base_url = "http://192.168.1.10:3301/"

def fixUrl(c, url):
    newsclass = c()
    step1 = re.search(newsclass.regex, url)
    if step1 == None:
        return
    step2 = newsclass.formatUrl(step1.group(0))
    return step2

@app.route('/<site>/<path:article>')
def articleView(site, article):
    with open("data.json") as f:
        data = json.load(f)
    sites = list(data.keys())
    if not site in sites:
        abort(404)
    fixedUrl = fixUrl(nameToClass[site], article)
    if fixedUrl != article and fixedUrl != None:
        return redirect(base_url+"{}/{}".format(site,fixedUrl))
    if not article in data[site]:
        return render_template("archive.html", site=site, article=article)
    articledata = data[site][article]
    return render_template("article.html", articledata=articledata)


@app.route('/archive/<site>/<path:article>')
def archiveView(site, article):
    with open("archive.json") as f:
        data = json.load(f)
    sites = list(data.keys())
    if not site in sites:
        abort(404)
    if not article in data[site]:
        abort(404)
    articledata = data[site][article]
    return render_template("article.html", articledata=articledata)
app.run(port='3301', host="0.0.0.0")
