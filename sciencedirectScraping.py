import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.common.action_chains import ActionChains
import random
import json
import signal
import sys
import argparse
import logging
from testBD import save_to_mongodb

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set up a global variable for articles data
articles_data = []

# Function to handle cleanup on exit
def save_data(query, signum=None, frame=None):
    logging.info("Saving collected articles data before exiting...")
    # Create a filename based on the query
    safe_query = query.replace(" ", "_")
    filename = f"ScienceDirect_{safe_query}_articles.json"
    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(articles_data, json_file, ensure_ascii=False, indent=4)
    sys.exit(0)

# Register the signal handler
signal.signal(signal.SIGINT, lambda signum, frame: save_data(args.query, signum, frame))

# Set up argument parser for query
parser = argparse.ArgumentParser(description="Scrape ScienceDirect articles based on a research topic.")
parser.add_argument("--query", type=str, required=True, help="Research topic to search for.")
args = parser.parse_args()

# Set up Chrome options
chrome_options = uc.ChromeOptions()
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-webgl")
chrome_options.add_argument("--disable-application-cache")

# Initialize undetected Chrome driver
try:
    driver = uc.Chrome(options=chrome_options)
except Exception as e:
    logging.error(f"Failed to initialize the Chrome driver: {e}")
    sys.exit(1)

# Random window size
width = random.randint(800, 1200)
height = random.randint(600, 800)
driver.set_window_size(width, height)
driver.set_window_position(random.randint(0, 100), random.randint(0, 100))

logging.info("Starting Chrome...")
driver.get("https://www.sciencedirect.com")
logging.info(driver.title)

# Hide WebDriver properties
driver.execute_script("""    
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'language', {get: () => 'en-US'}); 
    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
""")

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

while True:
    try:
        # Collect the links for the articles at each page or iteration
        def get_articles():
            articles = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.anchor.result-list-title-link"))
            )
            # Print all the articles
            print(articles)

            return articles

        # Check on each page
        articles = get_articles()

        for index in range( len(articles)):  # The count will be started from 13
            try:
                if index < len(articles):
                    logging.info(f"Processing article index: {index}")
                    articles = driver.find_elements(By.CSS_SELECTOR, "a.anchor.result-list-title-link")
                    article = articles[index]
                    article_url = article.get_attribute("href")
                    logging.info(f"Entering article: {article_url}")
                    driver.get(article_url)

                    article_data = {
                        "link": article_url,
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
                        logging.error(f"Could not extract journal name from {article_url}: {e}")

                    try:
                        article_title = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "span.title-text"))
                        ).text
                        article_data["article_title"] = article_title
                    except Exception as e:
                        logging.error(f"Could not extract article title from {article_url}: {e}")

                    try:
                        doi_element = WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "a.anchor.doi"))
                        )
                        doi_link = doi_element.get_attribute("href").replace("https://doi.org/", "")
                        article_data["doi"] = doi_link
                    except Exception as e:
                        logging.error(f"Could not extract DOI from {article_url}: {e}")

                    try:
                        doi_pub_date = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div.text-xs"))
                        ).text
                        article_data["publication_date"] = doi_pub_date
                    except Exception as e:
                        logging.error(f"Could not extract publication date from {article_url}: {e}")

                    try:
                        authors = driver.find_elements(By.CSS_SELECTOR, "span.react-xocs-alternative-link")
                        for author in authors:
                            try:
                                # Extract the author name
                                given_name = author.find_element(By.CLASS_NAME, 'given-name').text
                                surname = author.find_element(By.CLASS_NAME, 'surname').text
                                author_name = f"{given_name} {surname}"
                                author_button = author.find_element(By.XPATH, "../../..")

                                # Click to open the side panel for lab details
                                ActionChains(driver).move_to_element(author_button).click(author_button).perform()
                                time.sleep(1)  # Wait for the side panel to open

                                # Scrape lab affiliations
                                labs = []
                                try:
                                    lab_elements = driver.find_elements(By.CSS_SELECTOR, "div.side-panel .affiliation")
                                    labs = [lab.text for lab in lab_elements]
                                except Exception as e:
                                    logging.error(f"Error extracting affiliations for {author_name}: {e}")

                                # Store author data
                                article_data["authors_data"].append({"name": author_name, "labs": labs})

                            except Exception as e:
                                logging.error(f"Error processing author: {e}")
                    except Exception as e:
                        logging.error(f"Could not extract author data for {article_url}: {e}")

                    # Add the article to the collected data
                    articles_data.append(article_data)

            except Exception as e:
                logging.error(f"Error processing article index {index}: {e}")

       # Wait for the "next" button to be clickable
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "li.pagination-link.next-link a"))
        )
        if next_button:
            # Click the "next" button
            next_button.click()
            logging.info("Clicked the next button.")
        
            # Wait a random amount of time to simulate human behavior
            time.sleep(random.uniform(4, 8))
        else:
            break

    except Exception as e:
        logging.error(f"Error in while loop: {e}")

driver.quit()
