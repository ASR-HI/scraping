from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from dotenv import load_dotenv

load_dotenv()

chrome_driver_path = os.getenv("CHROME_DRIVER_PATH")

service = Service(executable_path=chrome_driver_path)
print("Starting")

driver = webdriver.Chrome(service=service)
driver.get("https://www.sciencedirect.com")
print(driver.title)

try:
    search = driver.find_element(By.ID, "qs")
    search.send_keys("llm")

    search_button = driver.find_element(By.CLASS_NAME, "button-primary")
    search_button.click()

    close_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "bdd-els-close"))
    )
    close_button.click()

except Exception as e:
    print(f"Error occurred: {e}")

time.sleep(10)

driver.quit()
