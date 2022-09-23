import os
from discord.ext import commands
from web_server import keep_alive

try:
  import pynacl
except ModuleNotFoundError:
  import sys
  import subprocess

  subprocess.check_call([sys.executable, "-m", "pip", "install",
                        "PyNaCl"])
  import nacl

PREFIX = '`'
COG = 'core_module_1.py'
TOKEN = os.environ['DISCORD_TOKEN']

def main():
  # Get a list of available cog extensions
  # Get path to cogs
  # Load discord bot
  bot = commands.Bot(command_prefix=PREFIX)
  # Load each cog
  bot.load_extension(COG[:-3])

  # Create web server to ping the bot
  keep_alive()
  # Run bot
  bot.run(TOKEN)

if __name__ == "__main__":
  main()
