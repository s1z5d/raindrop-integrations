#!/usr/bin/python3

import time
import os
import urllib
import re

import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import pyotp

from dotenv import load_dotenv
load_dotenv()

FB_EMAIL = os.getenv('FB_EMAIL')
FB_PASSWORD = os.getenv('FB_PASSWORD')
FB_OTP = os.getenv('FB_OTP')

RAINDROP_TOKEN = os.getenv('RAINDROP_TOKEN')

# TODO:
# - potentially use xpath counting to fix perf issue when looking for links while scrolling
#   - keep count of posts we've gone through and limit xpath search using them?
# - find way to fix total link count
# - error handling and reporting


option = Options()

option.add_argument("--disable-infobars")
option.add_argument("--disable-extensions")

# Pass the argument 1 to allow and 2 to block
option.add_experimental_option("prefs", { 
    "profile.default_content_setting_values.notifications": 1 
})

driver = webdriver.Chrome(chrome_options=option)
driver.get('https://www.facebook.com')

email_elem = driver.find_element_by_id('email')
email_elem.send_keys(FB_EMAIL)

email_elem = driver.find_element_by_id('pass')
email_elem.send_keys(FB_PASSWORD)
email_elem.send_keys(Keys.ENTER)

# get OTP
otp_elem = driver.find_element_by_id('approvals_code')
totp = pyotp.TOTP(FB_OTP)
otp_elem.send_keys(totp.now())
otp_elem.send_keys(Keys.ENTER)

# save browser prompt
driver.find_element_by_xpath("//input[@value='dont_save']").click()
driver.find_element_by_id('checkpointSubmitButton').click()

driver.get('https://www.facebook.com/saved')

# scroll to bottom of page https://stackoverflow.com/a/43299513
SCROLL_PAUSE_TIME = 3

# Get scroll height
last_height = driver.execute_script("return document.body.scrollHeight")

existing_links = []
with open('facebook.txt', 'a+') as f:
    f.seek(0)
    existing_links = f.read()

payloads = []
links = []
found = False
while True:
    # Grab links from titles (which always exist)
    # Unfortunately, we will grab _all_ the titles in a page after every scroll.
    # While this is mostly acceptable for incremental runs, it will be very slow for the first run.
    title_elems = driver.find_elements_by_xpath("/html/body/div[1]/div/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div[2]/div/div/div/div/div[2]/div/div/div/div/div[2]/a")
    _links = list(map(lambda e: e.get_attribute("href"), title_elems))
    # Grab "new" links -- these are the ones we might want to test
    new_links_to_test = list(filter(lambda l: l not in links, _links))
    # Thanks to Zuck, every link is now encoded with tracking data and not unique. Using an old plugin link, we can get a unique URL and check against existing links.
    # https://news.ycombinator.com/item?id=32118095
    for link in new_links_to_test:
        # "pfbid" denotes an encoded link
        # if the link is not encoded, we don't need to pass it through the plugin
        if "pfbid" in link:
            # Open new tab
            driver.execute_script("window.open()")
            tabs = driver.window_handles
            driver.switch_to.window(tabs[1])
            driver.get("https://www.facebook.com/plugins/post.php?href=" + link)
            # time.sleep(3) # Wait for page to load
            unique_link = driver.find_element_by_xpath("//a[contains(@href,'/posts/')]").get_attribute("href")
            # Close tab
            driver.execute_script("window.close()")
            driver.switch_to.window(tabs[0])
        else:
            unique_link = link

        cleaned_link = re.sub(r"[\?|&](fbclid|h)=.*", '', urllib.parse.unquote(unique_link.replace("https://l.facebook.com/l.php?u=", '')))
        if cleaned_link in existing_links: 
            found = True
            break
        
        # Try and grab "title"
        index = next(i for i, e in enumerate(title_elems) if e.get_attribute("href") == link) # Idiomatic...
        subtitle_elems = driver.find_elements_by_xpath("//a[contains(@href, '{}')]//..//span[contains(text(), 'Saved from')]//child::a[1]".format(link))
        if (len(subtitle_elems) == 0):
            # One of those weird saved posts that only contains a link, and no reference to a post...
            # We construct the payload accordingly
            title = title_elems[index].text # Use the main title as title
            tags = ['facebook'] if 'facebook.com' in cleaned_link else ['facebook_link']
            payload = {
                'link': cleaned_link,
                'tags': tags,
                'excerpt': title + '\n' + cleaned_link,
                'title': title
            }
            payloads.append(payload)
        else:
            title = subtitle_elems[0].text
            alt_title = title_elems[index].text
            payload = {
                'link': cleaned_link,
                'tags': ['facebook'],
                'excerpt': alt_title + '\n' + cleaned_link,
                'title': title + ' from Facebook'
            }
            payloads.append(payload)
    
    if found: break
    
    # Add the new links to the main list, since they have been checked
    links.extend(new_links_to_test)

    # Scroll down to bottom
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # Wait to load page
    time.sleep(SCROLL_PAUSE_TIME)

    # Calculate new scroll height and compare with last scroll height
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

driver.close()

n = len(payloads)
print('Adding {} links!'.format(n))

# add links to raindrop
headers = {
    'Authorization': 'Bearer ' +  RAINDROP_TOKEN,
}

with open('facebook.txt', 'a+') as f:
    f.seek(0)
    for i in range(len(payloads)):
        p = payloads[i]
        print(p['link'] + ' ' + str(i + 1) + '/' + str(n))
        f.write(p['link'] + '\n')
        r = requests.post('https://api.raindrop.io/rest/v1/raindrop', headers=headers, json=p)
        print(r.content)
        print()
        time.sleep(1)