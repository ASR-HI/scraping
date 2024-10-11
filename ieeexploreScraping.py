import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from dotenv import load_dotenv

load_dotenv()
chrome_driver_path = os.getenv("CHROME_DRIVER_PATH")
service = Service(executable_path=chrome_driver_path)
print("Starting")
driver = webdriver.Chrome(service=service)
driver.get("https://ieeexplore.ieee.org")
print(driver.title)

search =  driver.find_element(By.CLASS_NAME, 'Typeahead-input')
search.send_keys("llm")
search.send_keys(Keys.RETURN)


time.sleep(20)