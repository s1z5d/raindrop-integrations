#!/usr/bin/python3

import praw, pprint, requests, os, time
from dotenv import load_dotenv
load_dotenv()

REDDIT_USERNAME = os.getenv('REDDIT_USERNAME')
REDDIT_PASSWORD = os.getenv('REDDIT_PASSWORD')
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')

RAINDROP_TOKEN = os.getenv('RAINDROP_TOKEN')


reddit = praw.Reddit(client_id=REDDIT_CLIENT_ID,
                     client_secret=REDDIT_CLIENT_SECRET,
                     user_agent="test script",
                     username=REDDIT_USERNAME,
                     password=REDDIT_PASSWORD)


links = []
i = 0
with open('sub_list.txt', 'r') as f:
    subs = f.readlines()

for sub in subs:
    sub = sub.strip()
    print(sub)
    for item in reddit.user.me().saved(limit=None, params={'sr': sub}):
        i = i + 1
        if type(item) is praw.models.Submission:
            links.append({
                'link': item.permalink,
                'title': '[Reddit: ' + sub +  '] ' + item.title,
                'sub': sub,
                'content': item.url + '\n' + item.selftext
            })
            print(item.permalink)
        else:
            links.append({
                'link': item.permalink + '?context=10000',
                'title': '[Reddit Comment: ' + sub + '] ' + item.submission.title,
                'sub': sub,
                'content': item.body
            })
            print(item.permalink)
    print(i)

headers = {
    'Authorization': 'Bearer ' + RAINDROP_TOKEN
}

with open('reddit.txt', 'a+') as f:
    f.seek(0)
    existing_links = f.read()
    for i, link in enumerate(links):
        if link['link'] not in existing_links:
            f.write(link['link'] + '\n')
            payload = {
                'link': 'https://old.reddit.com' + link['link'],
                'tags': ['reddit'],
                'excerpt': 'https://old.reddit.com' + link['link'] + '\n' + link['content'],
                'title': link['title']
            }
            r = requests.post('https://api.raindrop.io/rest/v1/raindrop', headers=headers, json=payload)
            print(str(i) + ' of ' + str(len(links)))
            print(r.content)
            time.sleep(1)