import json

def extract_authors_with_labs(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    extracted_data = []

    for article in data:
        for author in article.get("authors_data", []):
            author_name = author.get("name", "").strip()
            for lab in author.get("labs", []):
                if lab.strip():  # Ignorer les chaînes vides
                    country = lab.split(",")[-1].strip()
                    extracted_data.append({
                        "name": author_name,
                        "lab": lab,
                        "country": country
                    })

    # Écriture dans un fichier JSON de sortie
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(extracted_data, file, ensure_ascii=False, indent=2)

# Chemin du fichier d'entrée et de sortie
input_file = "./finalScienceDirect.json"  # Chemin de votre fichier JSON d'origine
output_file = "./pays_ScinceDirect.json"          # Chemin du fichier de sortie

# Exécuter la fonction d'extraction
extract_authors_with_labs(input_file, output_file)

print(f"Les données ont été extraites et enregistrées dans '{output_file}'.")
