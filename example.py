import google.generativeai as genai
import os
import time
from dotenv import load_dotenv
from google.api_core import exceptions

# 1. Load environment variables
load_dotenv()

# 2. Configure the API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=api_key)

# 3. Initialize the model
model = genai.GenerativeModel("gemini-1.5-flash")

def safe_generate_content(prompt):
    """
    Attempts to generate content and waits if the rate limit is hit.
    """
    while True:
        try:
            response = model.generate_content(prompt)
            return response.text
        except exceptions.ResourceExhausted:
            # This handles the "Quota exceeded" error you saw
            print("Rate limit reached. Waiting 60 seconds to retry...")
            time.sleep(60) 
        except Exception as e:
            # This handles other potential errors (network, etc.)
            return f"An unexpected error occurred: {e}"

# 4. Execute
result = safe_generate_content("Hello")
print(result)