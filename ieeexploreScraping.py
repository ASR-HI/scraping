import time
import logging
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException , WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def initialize_driver():
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-extensions')
        options.add_argument('--proxy-server="direct://"')
        options.add_argument('--proxy-bypass-list=*')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-browser-side-navigation')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36")
        
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        logging.info("WebDriver initialized successfully.")
        return driver
    except WebDriverException as e:
        logging.error(f"Error initializing WebDriver: {e}")
        return None

def search_articles(driver, query):
    """Search for articles on IEEE Xplore."""
    driver.get("https://ieeexplore.ieee.org")
    logging.info(f"Navigated to {driver.current_url}")
    
    try:
        search = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.Typeahead-input[type='search']"))
        )
        search.send_keys(query)
        logging.info("Search query entered: %s", query)

        search_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button.fa-search"))
        )
        search_button.click()
        logging.info("Search submitted for query: %s", query)

    except TimeoutException:
        driver.save_screenshot("error_screenshot.png")
        logging.error("Search bar or button not found.")

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
        logging.info(f"Navigated to next page with button class: {class_name}")
        return True
    except TimeoutException:
        logging.warning(f"Next button not found for class: {class_name}")
        return False

def find_items(driver):
    """Find the result items on the current page and extract information."""
    try:
        elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "List-results-items"))
        )
        logging.info(f"Found {len(elements)} items on the current page.")
        articles_data = []

        for element in elements:
            article_data = {}
            title_element = element.find_element(By.CSS_SELECTOR, "h3.text-md-md-lh a.fw-bold")
            article_data['Title'] = title_element.text.strip()
            article_data['Link'] = title_element.get_attribute('href')

            logging.info(f"Extracting details for article: {article_data['Title']}")
            driver.execute_script("window.open(arguments[0], '_blank');", article_data['Link'])
            driver.switch_to.window(driver.window_handles[-1])

            article_data['Abstract'] = extract_abstract(driver)
            article_data['Details'] = extract_article_details(driver)
            expand_authors_section(driver)
            #authors_data = extract_authors_and_labs(driver)
            article_data['authors_data'] = extract_authors_and_labs(driver)

            expand_keywords_section(driver)
            article_data['keywords'] = extract_keywords(driver)


            
            articles_data.append(article_data)

            driver.close()
            driver.switch_to.window(driver.window_handles[0])

        return articles_data
    except TimeoutException:
        logging.error("No items found on the current page.")
        return []

def extract_abstract(driver):
    """Extract Abstract from the article's detail page."""
    try:
        try:
            show_more_button = driver.find_element(By.CSS_SELECTOR, "a.document-abstract-toggle-btn")
            show_more_button.click()
            logging.info("Clicked 'Show More' to display the full abstract.")
            time.sleep(2)
        except NoSuchElementException:
            logging.info("'Show More' button not found, proceeding to extract available abstract.")

        abstract_element = driver.find_element(By.CSS_SELECTOR, "div.abstract-desktop-div div.abstract-text")
        return abstract_element.text.strip()

    except NoSuchElementException:
        logging.error("Abstract element not found.")
        return None
    except Exception as e:
        logging.error(f"Error extracting abstract: {e}")
        return None

def extract_article_details(driver):
    """Extract additional article details."""
    details = {}

    # Extract DOI
    try:
        doi_element = driver.find_element(By.CSS_SELECTOR, "div.stats-document-abstract-doi a")
        details['DOI'] = doi_element.text.strip()
    except NoSuchElementException:
        logging.warning("DOI not found.")

    # Extract Date of Publication
    try:
        pub_date_element = driver.find_element(By.CSS_SELECTOR, "div.doc-abstract-pubdate")
        details['Date of Publication'] = pub_date_element.text.split(":")[-1].strip()
    except NoSuchElementException:
        logging.warning("Date of publication not found.")

    # Extract Publisher
    try:
        publisher_element = driver.find_element(By.CSS_SELECTOR, "div.doc-abstract-publisher span.title")
        publisher = publisher_element.find_element(By.XPATH, "following-sibling::span").text.strip()
        details['Publisher'] = publisher
    except NoSuchElementException:
        logging.warning("Publisher information not found.")

    # Extract Published In
    try:
        published_in_element = driver.find_element(By.CSS_SELECTOR, "div.stats-document-abstract-publishedIn a")
        details['Published In'] = published_in_element.text.strip()
    except NoSuchElementException:
        logging.warning("Published In information not found.")

    return details

def expand_authors_section(driver):
    """Expand the Authors section to display authors and their lab information."""
    try:
        authors_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "authors-header"))
        )
        authors_button.click()
        logging.info("Authors section expanded.")
        time.sleep(2)  # Ensure the content has time to load
    except NoSuchElementException:
        logging.error("Authors section not found.")

def extract_authors_and_labs(driver):
    """Extract authors and their associated lab information from the page."""
    authors_data = []
    
    try:
        # Locate the author sections
        author_items = driver.find_elements(By.CSS_SELECTOR, "xpl-author-item")
        
        for item in author_items:
            author_info = {}
            # Extract author name
            author_name = item.find_element(By.CSS_SELECTOR, "span").text.strip()
            if not author_name:  # Skip if the name is empty
                continue

            author_info["name"] = author_name
            
            # Extract lab information
            lab_elements = item.find_elements(By.CSS_SELECTOR, ".author-card div:nth-child(2) div")
            labs = [lab.text.strip() for lab in lab_elements if lab.text.strip()]
            author_info["labs"] = labs

            authors_data.append(author_info)

        logging.info(f"Extracted authors and labs: {authors_data}")
        return authors_data

    except NoSuchElementException:
        logging.error("No authors found.")
        return []
    except Exception as e:
        logging.error(f"Error extracting authors and labs: {e}")
        return []
def save_to_json(data, filename="articles_data.json"):
    """Save data to a JSON file."""
    try:
        with open(filename, "w") as file:
            json.dump(data, file, indent=4)
        logging.info(f"Data saved to {filename}")
    except Exception as e:
        logging.error(f"Failed to save data to {filename}: {e}")

def expand_keywords_section(driver):
    """Click the 'Keywords' button to expand the keywords section."""
    try:
        keywords_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "keywords-header"))
        )
        keywords_button.click()
        logging.info("Keywords section expanded.")
        time.sleep(2)  # Give time for the section to load
    except NoSuchElementException:
        logging.error("Keywords section not found.")
    except TimeoutException:
        logging.error("Keywords button click timed out.")

def extract_keywords(driver):
    """Extract Author and IEEE keywords from the page."""
    keywords = {
        "IEEE Keywords": [],
        "Author Keywords": []
    }
    
    try:
        # Locate the container with the keywords
        keyword_section = driver.find_elements(By.CSS_SELECTOR, "li.doc-keywords-list-item")
        
        # Extract Author Keywords
        for section in keyword_section:
            header = section.find_element(By.TAG_NAME, 'strong').text
            if header == "Author Keywords":
                author_keywords = section.find_elements(By.CSS_SELECTOR, "ul.List--inline li a")
                for keyword in author_keywords:
                    keywords["Author Keywords"].append(keyword.text.strip())

            # Extract IEEE Keywords
            elif header == "IEEE Keywords":
                ieee_keywords = section.find_elements(By.CSS_SELECTOR, "ul.List--inline li a")
                for keyword in ieee_keywords:
                    keywords["IEEE Keywords"].append(keyword.text.strip())
        
        logging.info(f"Extracted IEEE Keywords: {keywords['IEEE Keywords']}")
        logging.info(f"Extracted Author Keywords: {keywords['Author Keywords']}")
        return keywords

    except NoSuchElementException:
        logging.error("Keywords not found.")
        return keywords
    except Exception as e:
        logging.error(f"Error extracting keywords: {e}")
        return keywords
   
def main():
    """Main function to run the web scraping."""
    driver = initialize_driver()
    all_articles = []
    index = 2
    try:
        search_articles(driver, "llm")
        apply_filter(driver)

        while True:
            time.sleep(2)
            items = find_items(driver)
            if not items:
                break
            all_articles.extend(items)

            time.sleep(2)
            has_next = navigate_to_next_page(driver, index)
            index += 1
            if not has_next:
                break
    finally:
        save_to_json(all_articles)
        logging.info("Done")
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    main()
