import os 
from dotenv import load_dotenv
load_dotenv()

NEWSAPI_KEY = os.getenv("NEWS_API_KEY") 
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")