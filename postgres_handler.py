import psycopg2
from psycopg2.extras import Json
import yaml
import datetime

def get_connection():
    with open("config.yaml") as f:
        config=yaml.safe_load(f)['POSTGRES']
    connection=psycopg2.connect(user=config['USERNAME'], password=config['PASSWORD'], host=config['HOST'], port=config['PORT'], database="newsdiffs2")
    connection.autocommit=True
    return connection

def get_within_time(connection, org, days=7):
    cursor=connection.cursor()
    timestamp=datetime.datetime.now()-datetime.timedelta(days=days)
    cursor.execute("SELECT url FROM articles WHERE org=(%s) AND last_modified>(%s)",(org, timestamp))
    return cursor.fetchall()

class ArticleHandler:
    def __init__(self, url, connection=get_connection()):
        self.cursor=connection.cursor()
        self.databaseEntry=self.get_article(url)
        self.exists=self.databaseEntry is not None

    def get_article(self, url):
        self.cursor.execute("SELECT url, data FROM articles WHERE url=(%s)", (url,))
        return self.cursor.fetchone()
    
    def update_article(self, url, data):
        self.cursor.execute("UPDATE articles SET data=(%s), last_modified=(%s) WHERE url=(%s)", (Json(data), datetime.datetime.now(), url))
    
    def create_article(self, url, org, data):
        self.cursor.execute("INSERT INTO articles (url, org, last_modified, data) VALUES (%s,%s,%s,%s)", (url, org, datetime.datetime.now(), Json(data)))