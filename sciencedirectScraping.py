import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import json
import signal
import sys
import argparse
import logging
from selenium.webdriver.common.action_chains import ActionChains

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

articles_data = []  # To store detailed article information
article_links = []  # To store all article URLs

# Function to handle cleanup on exit
def save_data(query, signum=None, frame=None):
    logging.info("Saving collected articles data before exiting...")
    safe_query = query.replace(" ", "_")
    filename = f"ScienceDirect_{safe_query}_articles.json"
    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(articles_data, json_file, ensure_ascii=False, indent=4)
    sys.exit(0)

# Register the signal handler for cleanup on exit
signal.signal(signal.SIGINT, lambda signum, frame: save_data(args.query, signum, frame))

# Set up argument parser for query
parser = argparse.ArgumentParser(description="Scrape ScienceDirect articles based on a research topic.")
parser.add_argument("--query", type=str, required=True, help="Research topic to search for.")
args = parser.parse_args()

# Set up Chrome options for undetected_chromedriver
chrome_options = uc.ChromeOptions()
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-webgl")
chrome_options.add_argument("--disable-application-cache")

# Initialize the Chrome driver
try:
    driver = uc.Chrome(options=chrome_options)
except Exception as e:
    logging.error(f"Failed to initialize the Chrome driver: {e}")
    sys.exit(1)

logging.info("Starting Chrome...")
driver.get("https://www.sciencedirect.com")
logging.info(driver.title)

# Search for the provided query
try:
    search = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "input[id='qs']"))
    )
    search.send_keys(args.query)
    time.sleep(random.uniform(3, 7))
    
    # Click search button
    search_button = driver.find_element(By.CLASS_NAME, "button-primary")
    search_button.click()
    time.sleep(random.uniform(3, 7))

except Exception as e:
    logging.error(f"Could not search for '{args.query}': {e}")

# Enable "Review articles" filter
try:
    checkbox_container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//label[contains(@for, 'articleTypes-REV')]"))
    )
    driver.execute_script("arguments[0].scrollIntoView();", checkbox_container)
    time.sleep(2)

    review_checkbox = driver.find_element(By.XPATH, "//input[contains(@id, 'articleTypes-REV')]")
    if not review_checkbox.is_selected():
        driver.execute_script("arguments[0].click();", review_checkbox)
        time.sleep(random.uniform(4, 8))
        logging.info("Enabled 'Review articles' filter using JavaScript click.")
    else:
        logging.info("'Review articles' filter was already enabled.")
except Exception as e:
    logging.error("Could not enable 'Review articles' filter:", e)

# Enable "Research articles" filter
try:
    checkbox_container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//label[contains(@for, 'articleTypes-FLA')]"))
    )

    research_checkbox = driver.find_element(By.XPATH, "//input[contains(@id, 'articleTypes-FLA')]")
    if not research_checkbox.is_selected():
        driver.execute_script("arguments[0].click();", research_checkbox)
        time.sleep(random.uniform(4, 8))
        logging.info("Enabled 'Research articles' filter using JavaScript click.")
    else:
        logging.info("'Research articles' filter was already enabled.")
except Exception as e:
    logging.error("Could not enable 'Research articles' filter:", e)

# Enable "Open access" filter
try:
    checkbox_container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//label[contains(@for, 'accessTypes-openaccess')]"))
    )

    open_checkbox = driver.find_element(By.XPATH, "//input[contains(@id, 'accessTypes-openaccess')]")
    if not open_checkbox.is_selected():
        driver.execute_script("arguments[0].click();", open_checkbox)
        time.sleep(random.uniform(4, 8))
        logging.info("Enabled 'open access' filter using JavaScript click.")
    else:
        logging.info("'open access' filter was already enabled.")
except Exception as e:
    logging.error("Could not enable 'Open access' filter:", e)

# Function to collect all article links from the current page
def collect_article_links():
    try:
        articles = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.anchor.result-list-title-link"))
        )
        for article in articles:
            link = article.get_attribute("href")
            if link not in article_links:  # Avoid duplicates
                article_links.append(link)
        logging.info(f"Collected {len(articles)} article links from the current page.")
    except Exception as e:
        logging.error(f"Could not collect article links: {e}")

# Function to click the "Next" button
def go_to_next_page():
    try:
        # Faites défiler la page jusqu'au bouton
        next_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li.pagination-link.next-link a"))
        )
        driver.execute_script("arguments[0].scrollIntoView();", next_button)
        logging.info("Scrolled to the next button.")

        # Attendez quelques secondes pour que la page se charge correctement
        time.sleep(1)

        # Cliquez sur le bouton
        next_button.click()
        logging.info("Clicked the next button.")
        time.sleep(random.uniform(3, 7))
        return True
    except Exception as e:
        logging.error(f"Error while trying to click the next button: {e}")
        return False


# Collect links from all pages before processing
while True:
    # Collect links from the current page
    collect_article_links()

    # Go to the next page
    if not go_to_next_page():
        break

logging.info(f"Collected a total of {len(article_links)} article links.")

# Function to process a single article
def process_article(url):
    logging.info(f"Processing article: {url}")
    driver.get(url)
    article_data = {
        "link": url,
        "journal_name": "N/A",
        "article_title": "N/A",
        "doi": "N/A",
        "publication_date": "N/A",
        "abstract": "N/A",
        "keywords": "N/A",
        "authors_data": []
    }

    try:
        journal_name = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "publication-title"))
        ).text
        article_data["journal_name"] = journal_name
    except Exception as e:
        logging.error(f"Could not extract journal name from {url}: {e}")

    try:
        article_title = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.title-text"))
        ).text
        article_data["article_title"] = article_title
    except Exception as e:
        logging.error(f"Could not extract article title from {url}: {e}")

    try:
        doi_element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.anchor.doi"))
        )
        doi_link = doi_element.get_attribute("href").replace("https://doi.org/", "")
        article_data["doi"] = doi_link
    except Exception as e:
        logging.error(f"Could not extract DOI from {url}: {e}")

    try:
        pub_date = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.text-xs"))
        ).text
        article_data["publication_date"] = pub_date
    except Exception as e:
        logging.error(f"Could not extract publication date from {url}: {e}")
    
    # Abstract extraction
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".abstract.author"))
        )
        abstract_section = driver.find_element(By.CSS_SELECTOR, ".abstract.author")
        abstract_text_div = abstract_section.find_element(By.CSS_SELECTOR, ".u-margin-s-bottom")
        abstract = abstract_text_div.text if abstract_text_div else "N/A"
        article_data["abstract"] = abstract
    except Exception as e:
        logging.error(f"Could not extract abstract from {url}: {e}")

    try:
        keywords = driver.find_elements(By.CLASS_NAME, "keyword")
        keywords_list = ", ".join([keyword.text for keyword in keywords])
        article_data["keywords"] = keywords_list
    except Exception as e:
        logging.error(f"Could not extract keywords from {url}: {e}")

    try:
        authors = driver.find_elements(By.CSS_SELECTOR, "span.react-xocs-alternative-link")
        for author in authors:
            try:
                given_name = author.find_element(By.CLASS_NAME, 'given-name').text
                surname = author.find_element(By.CLASS_NAME, 'surname').text
                author_name = f"{given_name} {surname}"
                author_button = author.find_element(By.XPATH, "../../..")

                ActionChains(driver).move_to_element(author_button).click(author_button).perform()
                time.sleep(1)

                labs = []
                try:
                    lab_elements = driver.find_elements(By.CSS_SELECTOR, "div.side-panel .affiliation")
                    labs = [lab.text for lab in lab_elements]
                except Exception as e:
                    logging.error(f"Error extracting affiliations for {author_name}: {e}")

                article_data["authors_data"].append({"name": author_name, "labs": labs})

            except Exception as e:
                logging.error(f"Error processing author: {e}")
    except Exception as e:
        logging.error(f"Could not extract author data for {url}: {e}")

    articles_data.append(article_data)

# Process all collected articles
for article_link in article_links:
    process_article(article_link)


# Save the collected data
save_data(args.query)

# Close the browser
try:
    driver.quit()
except Exception as e:
    logging.error(f"Error closing the browser: {e}")
