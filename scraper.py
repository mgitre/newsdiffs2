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
            if (datetime.now()-lastDate).days >= 2:
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

def addToUnscraped(article, reason):
    with open("unscraped.txt","a") as f:
        f.write(article+" missing "+reason+"\n")

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
    
    
    def processArticle(self, article):
        try:
            html, url = getHTMLURL(article)
            if url!=article:
                global data
                url=self.formatUrl(re.search(self.regex, url).group(0))
                if article in data[self.name]:
                    data[self.name][url] = data[self.name].pop(article)
            
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
        self.regex = "https://www\.washingtonpost\.com/(?:politics|nation|world|elections|us-policy)/(?:[^/]*/)?\d{4}/\d{2}/\d{2}/(?:[^/]*/|[^.]*.html)"
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
        self.headlineMatches = [("h1",{"itemprop":"headline"})]
        self.subheadlineMatches = [("p", {"id":"article-summary"}),("p", {"class":"css-h99hf"})]
        self.bylineMatches = [("p",{"itemprop":"author"})]
        self.articlebodyMatches = [("section",{"itemprop":"articleBody"})]
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
        self.headlineMatches = [("div",{"data-key":"card-headline"})]
        self.subheadlineMatches = []
        self.bylineMatches = [("span",{"class":re.compile("Component-bylines-")})]
        self.articlebodyMatches = [("div",{"class":"Article"})]
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
