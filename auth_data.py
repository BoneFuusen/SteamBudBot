from dotenv import dotenv_values
from steam import Steam
from decouple import config

config0 = dotenv_values('.env')

token = config0["PY_BOT_TOKEN"]

KEY = config("STEAM_API_KEY")
steam = Steam(KEY)
