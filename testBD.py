import logging
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os



def save_to_mongodb(articles_data , collection_name):

    load_dotenv()
    uri = os.getenv("MONGO_URI")

    client = MongoClient(uri, server_api=ServerApi('1'))
    # save data to MongoDB
    try:
        client.admin.command('ping')
        logging.info("Pinged your deployment. You successfully connected to MongoDB!")
        db = client["scraping_data"]
        collection = db[collection_name]
        collection.insert_many(articles_data)
        logging.info(f"Saved {len(articles_data)} articles to MongoDB.")

    except Exception as e:
        logging.error(f"Could not save data to MongoDB: {e}")