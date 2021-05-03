#!/usr/bin/python3

import time
import os
import json
import urllib
import re

import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
import pyotp

from dotenv import load_dotenv
load_dotenv()

TWITTER_EMAIL = os.getenv('TWITTER_EMAIL')
TWITTER_PASSWORD = os.getenv('TWITTER_PASSWORD')
TWITTER_OTP = os.getenv('TWITTER_OTP')
TWITTER_USERNAME = os.getenv('TWITTER_USERNAME')

RAINDROP_TOKEN = os.getenv('RAINDROP_TOKEN')

option = Options()

option.add_argument("--disable-infobars")
option.add_argument("--disable-extensions")

# Pass the argument 1 to allow and 2 to block
option.add_experimental_option("prefs", { 
    "profile.default_content_setting_values.notifications": 1 
})

driver = webdriver.Chrome(options=option, executable_path="/usr/bin/chromedriver")
driver.get('https://www.twitter.com/login')

done = False
while not done:
    try:
        email_elem = driver.find_element_by_css_selector("input[name*='email']")
        done = True
    except NoSuchElementException:
        time.sleep(1)

email_elem.send_keys(TWITTER_EMAIL)

pass_elem = driver.find_element_by_css_selector("input[name*='pass']")
pass_elem.send_keys(TWITTER_PASSWORD)
pass_elem.send_keys(Keys.ENTER)

time.sleep(5)

if (driver.find_element_by_css_selector("input[name*='email']")):
    un_elem = driver.find_element_by_css_selector("input[name*='email']")
    un_elem.send_keys(TWITTER_USERNAME)
    pass_elem = driver.find_element_by_css_selector("input[name*='pass']")
    pass_elem.send_keys(TWITTER_PASSWORD)
    pass_elem.send_keys(Keys.ENTER)

time.sleep(5)

otp_elem = driver.find_element_by_id("challenge_response")
totp = pyotp.TOTP(TWITTER_OTP)
otp_elem.send_keys(totp.now())
otp_elem.send_keys(Keys.ENTER)


driver.get('https://twitter.com/i/bookmarks')

