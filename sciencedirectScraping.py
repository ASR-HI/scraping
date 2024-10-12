import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
driver = uc.Chrome(options=chrome_options)

# Random window size
width = random.randint(800, 1200)
height = random.randint(600, 800)
driver.set_window_size(width, height)
driver.set_window_position(random.randint(0, 100), random.randint(0, 100))

print("Starting Chrome...")
driver.get("https://www.sciencedirect.com")
print(driver.title)

# Hide WebDriver properties
driver.execute_script("""
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'language', {get: () => 'en-US'});
    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
""")

# Open a file to write the results
with open("science_direct_articles.txt", "w", encoding="utf-8") as file:
    try:
        # Wait for the search input and interact with it
        search = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input[id='qs']"))
        )
        search.send_keys("llm")
        time.sleep(random.uniform(2, 5))  # Random sleep to mimic human interaction

        # Click the search button
        search_button = driver.find_element(By.CLASS_NAME, "button-primary")
        search_button.click()
        time.sleep(random.uniform(2, 5))  # Random sleep

        while True:  # Loop through pages
            # Collect all article links on the results page
            articles = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.anchor.result-list-title-link"))
            )

            for index in range(0,len(articles)-1):
                # Re-fetch the article links after navigating back
                articles = driver.find_elements(By.CSS_SELECTOR, "a.anchor.result-list-title-link")
                article = articles[index]
                article_url = article.get_attribute("href")
                print(f"Entering article: {article_url}")
                
                # Navigate to the article page
                driver.get(article_url)

                # Extract the required information
                try:
                    # Journal Name
                    journal_name = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "publication-title"))
                    ).text

                    if not journal_name:
                        continue
                    # Article Title
                    article_title = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "span.title-text"))
                    ).text

                    # DOI and Publication Date
                    doi_pub_date = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.text-xs"))
                    ).text

                    # Authors
                    authors = driver.find_elements(By.CSS_SELECTOR, "span.react-xocs-alternative-link")
                    authors_list = ", ".join([f"{author.find_element(By.CLASS_NAME, 'given-name').text} {author.find_element(By.CLASS_NAME, 'surname').text}" for author in authors])

                    # Affiliations (Labs)
                    affiliations = driver.find_elements(By.CSS_SELECTOR, "dl.affiliation dd")
                    affiliations_list = "\n".join([affiliation.text.replace("&amp;", "&").strip() for affiliation in affiliations])

                    # Abstract
                    # Abstract
                    abstract = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.abstract.author div[id^='d1e'] > div"))
                    ).text

                    # Keywords
                    keywords = driver.find_elements(By.CLASS_NAME, "keyword")
                    keywords_list = ", ".join([keyword.text for keyword in keywords])

                    # Write to file
                    file.write(f"Nom Journal: {journal_name}\n")
                    file.write(f"Titre de l'article: {article_title}\n")
                    file.write(f"DOI + Date de Publication: {doi_pub_date}\n")
                    file.write(f"Auteurs: {authors_list}\n")
                    file.write(f"Labos: {affiliations_list}\n")
                    file.write(f"Abstract: {abstract}\n")
                    file.write(f"Mots-clés: {keywords_list}\n")
                    file.write("\n" + "-" * 50 + "\n\n")  # Separator between articles

                except Exception as e:
                    print(f"Could not extract information from {article_url}: {e}")

                # Go back to the search results page
                driver.back()
                time.sleep(random.uniform(2, 5))  # Wait before going to the next article

                # Wait for the search results to be visible again
                WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "input[id='qs']"))
                )

                # Check for the "Next" button
            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-aa-region='srp-pagination']"))
                )
                next_button.click()  # Click the "Next" button
                time.sleep(random.uniform(2, 5))  # Random sleep
            except Exception as e:
                print("No more pages to navigate.")
                break  # Break the loop if there are no more pages

    except Exception as e:
        print(f"Error occurred: {e}")

time.sleep(600)
driver.quit()
