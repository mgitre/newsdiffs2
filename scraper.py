# -*- coding: utf-8 -*-
"""
Created on Wed Sep  9 10:13:04 2020

@author: Max
"""

import requests
import re
import json
from datetime import datetime
from bs4 import BeautifulSoup
from functools import partial
import concurrent.futures
import emailclient
import postgres_handler
import yaml

with open("config.yaml") as f:
    config=yaml.safe_load(f)

path=config['SERVER']['ACCESS']
use_email=config['EMAIL']['USE_EMAIL']

connection=postgres_handler.get_connection()

#headers to (mostly) get around bot detection, i still recommend using a VPN
def getHTML(url):
    headers = [{
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36 Edg/85.0.564.44",
        "X-Amzn-Trace-Id": "Root=1-5f592eba-58fbe130d46d9e0ebd201bdc"
    }]
    request = requests.get(url, headers=headers[0])
    return request.text

#same as above, except in the case of a redirect, returns final url
def getHTMLURL(url):
    headers = [{
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36 Edg/85.0.564.44",
        "X-Amzn-Trace-Id": "Root=1-5f592eba-58fbe130d46d9e0ebd201bdc"
    }]
    request = requests.get(url, headers=headers[0])
    return request.text, request.url

#change this to be whatever you want
def alert(message):
    print("NEW MESSAGE!!! "+message)

#logs articles that had issues with scraping
def addToUnscraped(article, reason):
    with open("unscraped.txt","a") as f:
        f.write(article+" missing "+reason+"\n")


#establishes base methods for each site, making it fairly easy to add new websites to scrape
class BaseScraper:
    def __init__(self):
        pass
    #goes to homepage of website and finds all urls that match the given regex pattern
    def getArticles(self):
        articles = []
        for initialpage in self.initialpages:
            homepage = BeautifulSoup(getHTML(initialpage), features="lxml")
            aelements = homepage.findAll("a", {"href": re.compile(".+")})
            for a in aelements:
                valid = re.search(self.regex, a["href"])
                if valid == None:
                    continue
                url = self.formatUrl(valid.group(0))
                exclude = False
                for exclusion in self.exclusions:
                    if url.find(exclusion) != -1:
                        exclude = True
                if exclude:
                    continue
                if not url in articles:
                    articles.append(url)
        for url, in postgres_handler.get_within_time(connection, self.name):
            if not url in articles:
                articles.append(url)
        return articles
    
    #adds an article to the site's data dictionary
    def addToData(self, article, articledata):
        global justchanged
        if articledata == None:
            return
        article_handler=postgres_handler.ArticleHandler(article, connection)
        if article_handler.exists:
            in_db=article_handler.databaseEntry[1]
            latest_in_db=list(in_db.keys())[-1]
            latest_entry=in_db[latest_in_db]

            has_changed=False
            has_fixed_missing=False
            for key in articledata:
                if articledata[key]==None:
                    articledata[key]=latest_entry[key]
                    continue
                if latest_entry[key]==None:
                    latest_entry[key]=articledata[key]
                    has_fixed_missing=True
                    continue
                if articledata[key]!=latest_entry[key]:
                    has_changed=True
            if has_changed:
                in_db.update({datetime.now().strftime("%m/%d/%Y, %H:%M:%S"):articledata})
                article_handler.update_article(article, in_db)
                alert(article)
                justchanged.append(self.name, article, articledata['headline'])
            elif has_fixed_missing:
                in_db[datetime.now().strftime("%m/%d/%Y, %H:%M:%S")] = in_db.pop(latest_in_db)
                article_handler.update_article(article, in_db)

        else:
            article_handler.create_article(article, self.name, {datetime.now().strftime("%m/%d/%Y, %H:%M:%S"):articledata})
        
    #scrapes an article given a URL
    def processArticle(self, article):
        try:
            html, url = getHTMLURL(article)
            print(url)
            soup = BeautifulSoup(html, features="lxml")
            
            #loads the headline
            headline = None
            for name, attrs in self.headlineMatches:
                matchAttempt = soup.find(name,attrs)
                if matchAttempt:
                    headline = matchAttempt.get_text()
                    break
            if not headline:
                addToUnscraped(url, "headline")
            #loads the byline(s)
            byline=None
            for name, attrs in self.bylineMatches:
                matchAttempt = soup.find(name, attrs)
                if matchAttempt:
                    bylinesoup = matchAttempt
                    #fix to get rid of annoying extra text
                    for hidden in bylinesoup.find_all(attrs={"class":"hidden"}):
                        hidden.decompose()
                    byline = bylinesoup.get_text().replace(u'\xa0',' ')
                    break
            
            
            #loads the subheadline
            subheadline = None
            for name, attrs in self.subheadlineMatches:
                matchAttempt = soup.find(name,attrs)
                if matchAttempt:
                    subheadline = matchAttempt.get_text()
                    break
            
            #loads article body
            content = None
            for name, attrs in self.articlebodyMatches:
                articlebody = soup.find(name, attrs)
                if articlebody:
                    paragraphs=[]
                    for paragraph in articlebody.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                        text = paragraph.get_text()
                        if text=="Read more:":
                            break
                        else:
                            paragraphs.append("<{0}>{1}</{0}>".format(paragraph.name, text))
                    content = "\n".join(paragraphs)
                    break
            if not content:
                addToUnscraped(url, "content")
            return url, {"headline":headline, "subheadline":subheadline, "byline":byline, "body":content}
        except Exception as e:
            print(e)

class WashingtonPost(BaseScraper):
    def __init__(self):
        self.regex = "https://www\.washingtonpost\.com/(?:politics|nation|world|elections|us-policy)/(?:[^/]*/)?(?:[^/]*/)?\d{4}/\d{2}/\d{2}/(?:[^/]*/|[^.]*.html)"
        self.initialpages = ["https://washingtonpost.com"]
        self.name = "washingtonpost"
        self.exclusions = ['live-updates']
        self.headlineMatches = [("h1",{"data-qa":"headline"}),("h1", {"class":"title"}),("h1",{"itemprop":"headline"})]
        self.subheadlineMatches = [("h2", {"data-pb-field":"subheadlines.basic"}),("h2", {"data-qa":"subheadline"})]
        self.bylineMatches = [("div",{"class":"author-names"}), ("div",{"class":"contributor"})]
        self.articlebodyMatches = [("div",{"class":"article-body"}),("article", {"data-qa":"main"}), ("div",{"class":"main"})]
        BaseScraper.__init__(self)
            
        
    def formatUrl(self, url):
        return url


class NewYorkTimes(BaseScraper):
    def __init__(self):
        self.regex = "^(?:https://(?:www\.)nytimes\.com)?/\d{4}/\d{2}/\d{2}/[^.]+.html"
        self.initialpages = ['https://nytimes.com',
                             'https://www.nytimes.com/section/todayspaper']
        self.name = "nytimes"
        self.exclusions = ['interactive']
        self.headlineMatches = [("h1",{"itemprop":"headline"}), ("h1",{"data-testid":"headline"}), ("h1",{"class":"edye5kn2"})]
        self.subheadlineMatches = [("p", {"id":"article-summary"}),("p", {"class":"css-h99hf"})]
        self.bylineMatches = [("p",{"itemprop":"author"}),("div",{"class":"css-vp77d3"})]
        self.articlebodyMatches = [("section",{"itemprop":"articleBody"}), ("section",{"name":"articleBody"})]
        BaseScraper.__init__(self)
        

    def formatUrl(self, url):
        if url[0] == '/':
            return "https://www.nytimes.com" + url
        return url

class APNews(BaseScraper):
    def __init__(self):
        self.regex = "(?:https://apnews\.com)?/article/.+[a-z0-9]{32}$"
        self.initialpages = ["https://apnews.com"]
        self.name = "apnews"
        self.exclusions = []
        self.headlineMatches = [("div",{"data-key":"card-headline"}),("div",{"class":re.compile("headline-")})]
        self.subheadlineMatches = []
        self.bylineMatches = [("span",{"class":re.compile("Component-bylines-")}), ("div",{"class":re.compile("byline-")})]
        self.articlebodyMatches = [("div",{"class":"Article"}),("article",{"class":re.compile("article-")})]
        BaseScraper.__init__(self)

    
    def formatUrl(self, url):
        formatted = url
        if url[0] == '/':
            formatted = "https://apnews.com" + url
        searched = re.search("https://apnews\.com/(article/.+)[a-z0-9]{32}$", formatted)
        if searched != None:
            groups = searched.groups()
            if len(groups)!=0:
                formatted = formatted.replace(groups[0],"")
        return formatted


#function to enable multithreaded downloading/processing of articles
def multiThreadCompatibility(scraper, article):
    processed = scraper.processArticle(article)
    if processed != None:
        url, articledata = processed
        scraper.addToData(url, articledata)

if __name__ == "__main__":
    scrapers = [WashingtonPost(), NewYorkTimes(), APNews()]
    if use_email:
        eclient=emailclient.CustomEmail()
    for scraper in scrapers:
        justchanged = []
        articles = scraper.getArticles()
        func = partial(multiThreadCompatibility, scraper)
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(articles)) as executor:
            executor.map(func, articles)
        if len(justchanged) > 0 and use_email:
            eclient.addHeader(scraper.name)
            for changed in justchanged:
                eclient.addArticle(changed)