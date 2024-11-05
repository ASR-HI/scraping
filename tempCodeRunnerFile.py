import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Charger les données du fichier JSON avec un encodage spécifique
with open('science_direct_articles.json', 'r', encoding='utf-8') as file:
    articles = json.load(file)

# Initialiser le driver
driver = webdriver.Chrome()  # Assurez-vous d'avoir le bon chemin du driver

# Fonction pour scraper les données d'un journal
def scrape_journal_data(journal_name):
    # Étape 1 : Accéder au site Scimago
    driver.get("https://www.scimagojr.com/")
    wait = WebDriverWait(driver, 10)

    # Étape 2 : Recherche du journal par nom
    search_box = wait.until(EC.visibility_of_element_located((By.ID, "searchinput")))
    search_box.clear()
    search_box.send_keys(journal_name)
    search_box.send_keys(Keys.RETURN)

    # Étape 3 : Sélectionner le lien du journal dans les résultats de recherche
    try:
        journal_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'journalsearch.php') and contains(@href, 'sid')]")))
        journal_link.click()
    except Exception as e:
        print(f"Erreur lors de la sélection du journal '{journal_name}': {e}")
        return None  # Passer au prochain journal

    # Étape 4 : Fermer l'annonce si elle est présente
    try:
        close_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "ns-jhssl-e-5.close-button"))
        )
        close_button.click()
        print("Annonce fermée.")
    except Exception as e:
        print("Pas d'annonce à fermer ou erreur :", e)

    # Scraper issn :
    try:
        issn = driver.find_element(By.XPATH, "//h2[text()='ISSN']/following-sibling::p")
        print(f"ISSN pour '{journal_name}': {issn.text}")
    except Exception as e:
        print(f"Erreur lors du scraping de l'ISSN pour '{journal_name}': {e}")

    # Étape 5 : Sélectionner et cliquer sur le bouton du tableau
    try:
        table_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".combo_buttons .combo_button.table_button"))
        )
        table_button.click()
    except Exception as e:
        print(f"Erreur lors de la sélection du tableau pour '{journal_name}': {e}")
        return None  # Passer au prochain journal

    # Attendre un peu pour que le tableau se charge complètement
    time.sleep(2)

    # Étape 6 : Scraper les données du tableau
    try:
        table = driver.find_element(By.XPATH, "//div[@class='cellslide']/table")
        rows = table.find_elements(By.XPATH, ".//tbody/tr")
        data = []

        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) == 3:
                category = cols[0].text.strip()
                year = cols[1].text.strip()
                quartile = cols[2].text.strip()
                if category and year and quartile:
                    data.append([category, year, quartile])

       

        # Transformer en DataFrame pour mieux visualiser
        df = pd.DataFrame(data, columns=["Category", "Year", "Quartile"])
        df['ISSN'] = issn.text  # Ajouter une colonne pour les ISSN
        print(df)

        # Exporter les données vers un fichier CSV
        df.to_csv(f"{journal_name.replace(' ', '_')}_ranking_data.csv", index=False)
        print(f"Les données pour '{journal_name}' ont été enregistrées dans {journal_name.replace(' ', '_')}_ranking_data.csv")
    except Exception as e:
        print(f"Erreur lors du scraping des données du tableau pour '{journal_name}': {e}")

# Boucle à travers chaque article et scraper les données
for article in articles:
    journal_name = article['journal_name']
    print(f"Traitement du journal: {journal_name}")
    scrape_journal_data(journal_name)

# Fermer le navigateur
driver.quit()
