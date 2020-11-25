# -*- coding: utf-8 -*-
"""
Created on Wed Sep  9 10:13:04 2020

@author: Max
"""

import requests
import re
#import random
import json
from datetime import datetime
from bs4 import BeautifulSoup
from functools import partial
import concurrent.futures
path = "http://192.168.1.10:3301/"

def cleanUp(data, archive):
    for site in data:
        archive[site] = archive.get(site,{})
        toPop = []
        for article in data[site]:
            lastDate = datetime.strptime(list(data[site][article].keys())[-1], '%m/%d/%Y, %H:%M:%S')
            if (datetime.now()-lastDate).days >= 1:
                print(article, end=" ")
                if len(data[site][article]) > 1:
                    if article in archive[site]:
                        for articleVersion in data[site][article]:
                            if data[site][article][articleVersion] != list(archive[site][article].values())[-1]:
                                archive[site][article].update(data[site][article][articleVersion])
                        #data[site].pop(article)
                        #toPop.append(article)
                        print("was updated in archive")
                    else:
                        archive[site][article] = data[site][article]
                        print("was added to archive")
                        #toPop.append(article)
                else:
                    print("was deleted")
                toPop.append(article)
        for article in toPop:
            data[site].pop(article)
    return data, archive
                #if 
            #print((datetime.now()-lastDate).days > 1)
            


# This just uses cool headers to download the HTML of a given URL.
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


def alert(message):
    print("NEW MESSAGE!!! "+message)


class BaseScraper:
    def __init__(self):
        self.data = data.get(self.name, {})

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
        for url in list(self.data.keys()):
            if not url in articles:
                articles.append(url)
        return articles
    def addToData(self, article, articledata):
        global justchanged
        if articledata == None:
            return
        global data
        self.data = data.get(self.name, {})
        dtime = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        articledata = {dtime: articledata}
        self.data[article] = self.data.get(article, articledata)
        latestdata = list(articledata.values())[-1]
        if latestdata != list(self.data[article].values())[-1]:
            self.data[article].update(articledata)
            if len(self.data[article]) > 1:
                alert(article)
                #print(articledata)
                justchanged.append((self.name,article, latestdata["headline"], len(self.data[article])))
        return self.data


class WashingtonPost(BaseScraper):
    def __init__(self):
        self.regex = "https://www\.washingtonpost\.com/(?:politics|nation|world|elections|us-policy)/(?:[^/]*/)?\d{4}/\d{2}/\d{2}/(?:[^/]*/|[^.]*.html)"
        self.initialpages = ["https://washingtonpost.com"]
        self.name = "washingtonpost"
        self.exclusions = ['live-updates']
        BaseScraper.__init__(self)

    def processArticle(self, article):
        try:
            html, url = getHTMLURL(article)
            if url != article:
                try:
                    url = self.formatUrl(re.search(self.regex, url).group(0))
                except:
                    return
                if article in data:
                    data[self.name][url] = data[self.name].pop(article)
                article = url
            print(article)
            soup = BeautifulSoup(html, features="lxml")
            headline = soup.find("h1", {"data-qa": "headline"}).get_text()
    
            # messy way of saying "if subhead exists, subhead is subhead, if not, it's none"
            subhead = soup.find(attrs={"data-qa": "subheadline"})
            if subhead != None:
                subhead = subhead.get_text()
    
            # this finds the main section of the article
            articlebody = soup.find("div", {"class": "article-body"})
            paragraphs = []
            for paragraph in articlebody.find_all():
                if paragraph.name in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    text = paragraph.get_text(strip=False)
                    if text == "Read more:":
                        break
                    else:
                        paragraphs.append(
                            "<{0}>{1}</{0}>".format(paragraph.name, paragraph.get_text()))
            content = '\n'.join(paragraphs)
            return article, {"headline": headline, "subhead": subhead, "body": content}
        except Exception as e:
            print(e)
            return

    def formatUrl(self, url):
        return url


class NewYorkTimes(BaseScraper):
    def __init__(self):
        self.regex = "^(?:https://(?:www\.)nytimes\.com)?/\d{4}/\d{2}/\d{2}/[^.]+.html"
        self.initialpages = ['https://nytimes.com',
                             'https://www.nytimes.com/section/todayspaper']
        self.name = "nytimes"
        self.exclusions = ['interactive']
        BaseScraper.__init__(self)

    def processArticle(self, article):
        print(article)
        html, url = getHTMLURL(article)
        if url != article:
            try:
                url = self.formatUrl(re.search(self.regex, url).group(0))
            except:
                return
            if article in data:
                data[self.name][url] = data[self.name].pop(article)
            article = url
        soup = BeautifulSoup(html, features="lxml")
        try:
            headline = soup.find("h1", {"itemprop": "headline"}).get_text()
        except:
            try:
                headline = soup.find("meta", {"property": "og:title"})[
                    "content"]
            except:
                headline = None
        try:
            subhead = soup.find(attrs={"id": "article-summary"}).get_text()
        except:
            try:
                subhead = soup.find("meta", {"name": "description"})["content"]
            except:
                subhead = None
        try:
            
            articlebodies = soup.findAll(
                "div", {"class": "StoryBodyCompanionColumn"})
            paragraphs = []
            for div in articlebodies:
                for paragraph in div.findAll():
                    if paragraph.name in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        paragraphs.append(
                            "<{0}>{1}</{0}>".format(paragraph.name, paragraph.get_text()))
            content = '\n'.join(paragraphs)
            return article, {"headline": headline, "subhead": subhead, "body": content}
        except Exception as e:
            print(e)
            return

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
        BaseScraper.__init__(self)

    def processArticle(self, article):
        try:
            html, url = getHTMLURL(article)
            if url != article:
                try:
                    url = self.formatUrl(re.search(self.regex, url).group(0))
                except:
                    return
                if article in data:
                    data[self.name][url] = data[self.name].pop(article)
                article = url
            print(article)
            soup = BeautifulSoup(getHTML(article), features="lxml")
            headline = soup.find("div",{"class":"CardHeadline"}).find("h1").get_text()
    
            subhead = None
    
            # this finds the main section of the article
            articlebody = soup.find("div", {"class": "Article"})
            paragraphs = []
            for paragraph in articlebody.find_all():
                if paragraph.name in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    paragraphs.append(
                        "<{0}>{1}</{0}>".format(paragraph.name, paragraph.get_text()))
            content = '\n'.join(paragraphs)
            return article, {"headline": headline, "subhead": subhead, "body": content}
        except Exception as e:
            print(e)
            return

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




with open('data.json') as f:
    data = json.load(f)

def multiThreadCompatibility(scraper, article):
    processed = scraper.processArticle(article)
    if processed != None:
        url, articledata = processed
        toAdd = scraper.addToData(url, articledata)
        if toAdd != None:
            data[scraper.name] = toAdd

def writeToFile(data, file="data.json"):
    with open(file, 'w', encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4)

if __name__ == "__main__":
    
    justchanged = []
    
    scrapers = [WashingtonPost(), NewYorkTimes(), APNews()]
    
    for scraper in scrapers:
        justchanged = []
        articles = scraper.getArticles()
        func = partial(multiThreadCompatibility, scraper)
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(articles)) as executor:
            executor.map(func, articles)
   
    
    with open('archive.json') as f:
        archive = json.load(f)

    data, archive = cleanUp(data, archive)
    writeToFile(data)
    writeToFile(archive, 'archive.json')
