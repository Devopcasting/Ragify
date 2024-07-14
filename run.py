import os
from dotenv import load_dotenv
from app import app

# Load environment variables from a .env file if it exists
load_dotenv()

# Determine the configuration to use based on an environment variable
config_name = os.environ.get('FLASK_ENV')

if __name__ == '__main__':
    app.run()
