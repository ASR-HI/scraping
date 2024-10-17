import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from selenium.webdriver.common.action_chains import ActionChains

load_dotenv()
chrome_driver_path = os.getenv("CHROME_DRIVER_PATH")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def initialize_driver():
    """Initialize the Chrome WebDriver."""
    logging.info("Starting WebDriver")
    service = Service(executable_path=chrome_driver_path)
    driver = webdriver.Chrome(service=service)
    return driver

def search_articles(driver, query):
    """Search for articles on IEEE Xplore."""
    driver.get("https://ieeexplore.ieee.org")
    logging.info(f"Navigated to {driver.current_url}")
    try:
        search = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'Typeahead-input'))
        )
        search.send_keys(query)
        search.send_keys(Keys.RETURN)
        logging.info("Search submitted for query: %s", query)
    except TimeoutException:
        logging.error("Search bar not found.")

def apply_filter(driver):
    """Apply the filter for early access articles."""
    try:
        early_access_checkbox = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "refinement-ContentType:Early Access Articles"))
        )
        if not early_access_checkbox.is_selected():
            early_access_checkbox.click()
            logging.info("Early Access Articles filter applied.")
        
        apply_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Apply')]"))
        )
        apply_button.click()
        logging.info("Filters applied.")
    except (NoSuchElementException, TimeoutException):
        logging.error("Failed to apply the filter for early access articles.")

def navigate_to_next_page(driver, index):
    """Navigate to the next page of results."""
    class_name = f"stats-Pagination_arrow_next_{index}"
    try:
        btn_next = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CLASS_NAME, class_name))
        )
        btn_next.click()
        logging.info("Navigated to next page with button class: %s", class_name)
        return True
    except TimeoutException:
        logging.warning("Next button not found for class: %s", class_name)
        return False

def find_items(driver):
    """Find the result items on the current page."""
    try:
        elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "List-results-items"))
        )
        logging.info(f"Found {len(elements)} items on the current page.")
        titles = []
        for element in elements:
            title_element = element.find_element(By.CSS_SELECTOR, "h3.text-md-md-lh a.fw-bold")
            title_text = title_element.text.strip() 
            titles.append(title_text)
            link = title_element.get_attribute('href') 
            print(title_text)
            print(link)
            driver.execute_script("window.open(arguments[0], '_blank');", link)
            driver.switch_to.window(driver.window_handles[-1])
            
            logging.info(f"Navigated to {link}")
            try:
                abstract = extract_additional_info(driver)  
            except Exception as e:
                logging.error(f"Failed to extract abstract from {link}: {e}")
                abstract = None
            print(abstract)
            
            driver.close()  
            driver.switch_to.window(driver.window_handles[0]) 
        return elements
    except TimeoutException:
        logging.error("No items found on the current page.")
        return []

def extract_additional_info(driver):
    """Extract additional information from the item's detail page (e.g., Abstract)."""
    try:
        try:
            show_more_button = driver.find_element(By.CSS_SELECTOR, "a.document-abstract-toggle-btn")
            show_more_button.click()
            logging.info("Clicked 'Show More' to display the full abstract.")
            time.sleep(2) 
        except NoSuchElementException:
            logging.info("'Show More' button not found, proceeding to extract available abstract.")
        
        abstract_element = driver.find_element(By.CSS_SELECTOR, "div.abstract-desktop-div div.abstract-text")
        abstract_text = abstract_element.text.strip()
        return abstract_text

    except NoSuchElementException:
        logging.error("Abstract element not found.")
        return None
    except Exception as e:
        logging.error(f"Error extracting abstract: {e}")
        return None



def main():
    """Main function to run the web scraping."""
    driver = initialize_driver()
    index = 2
    try:
        search_articles(driver, "llm")
        apply_filter(driver)

        while True:
            time.sleep(2)  
            items = find_items(driver)
            if not items:
                break  

            time.sleep(2)  
            has_next = navigate_to_next_page(driver,index)
            index = index + 1 
            if not has_next:
                break
    finally:
        logging.info("Done")
        time.sleep(5)  
        driver.quit()

if __name__ == "__main__":
    main()
