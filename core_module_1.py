import os
import discord
import pytube
import youtube_dl
import tracemalloc
import pandas as pd
import asyncio
import uuid
import requests
import nacl
import ffmpeg

from ffmpeg import FFmpeg
from replit import db
from discord.ext import commands
from discord.ext.commands import has_permissions
from discord.utils import get


try:
  from discord import FFmpegPCMAudio
except ModuleNotFoundError:
  import sys
  import subprocess

  subprocess.check_call([sys.executable, "-m", "pip", "install",
                        "python-ffmpeg"])

tracemalloc.start()

class Core_V1(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
    self.music_library = MusicLibraryManager()

  @commands.Cog.listener()
  async def on_ready(self):
    await self.bot.wait_until_ready()
    print("Logged in as {}".format(self.bot))

  
  
  @commands.command(name="play")
  @has_permissions(send_messages=True)
  async def play(self, ctx: commands.Context):
    """Checks whether a song exists to play, if not then
       It should download the song first.
    Params:
            check_library: the music index lookup, and from which
            the song will be retrieved or downloaded to it."""
    url = ctx.message.content.replace("play ", "")
    channel = ctx.message.author.voice.channel
    voice = get(self.bot.voice_clients, guild=ctx.guild)
    
    if voice and voice.is_connected():
      await voice.move_to(channel)
      await ctx.channel.send("Moved to channel {}".format(channel))
    else:
      voice = await channel.connect()
      await ctx.channel.send("Joined channel {}".format(channel))

    song = self.music_library.fetch_song(url=url)
    stop_event = asyncio.Event()
    loop = asyncio.get_event_loop()
    def after(error):
      if error:
        print("Error: {}".format(error))
      def clear():
        stop_event.set()
      loop.call_soon_threadsafe(clear)
      
    voice.play(discord.FFmpegPCMAudio(song), after=after)
    voice.source = discord.PCMVolumeTransformer(voice.source)
    voice.is_playing()

    await stop_event.wait()
    await voice.disconnect()

  @commands.command(name="skip")
  @has_permissions(send_messages=True)
  async def skip_song(self, ctx: commands.Context):
    voice = get(self.bot.voice_clients, guild=ctx.guild)
    voice.stop()
    await ctx.channel.send("Skipped song")

  @commands.command()
  @has_permissions(send_messages=True)
  async def leave(self, ctx: commands.Context):
    await ctx.voice_client.disconnect()


class MusicLibraryManager:
  def __init__(self):
    self.library_path = os.path.join(os.getcwd(), "music_data")
    self.meta_data_path = os.path.join(self.library_path, "meta_data.csv")

  def fetch_song(self, url):
    """Creates library index if it doesnt exist, and if it does
       then it searches the library for the requested song
    Returns:
            Path to the song"""
    if os.path.exists(self.meta_data_path):
      # Load music library index
      music_index = pd.read_csv(self.meta_data_path)
    else:
      # If call enters this block then it means theres
      # no music library
      meta_data = self.download_song(url=url)
      music_index = [[meta_data["id"], 
                     meta_data["path"], 
                     meta_data["origin"]]]
      music_index = pd.DataFrame(data=music_index,
                                 columns=["id", "path", "origin"])
      print(f'DF: {music_index}')
      music_index.to_csv(path_or_buf=self.meta_data_path,
                         columns=["id", "path", "origin"])
      print(music_index["path"], "\n", type(music_index["path"]))
      return music_index["path"][0]
    # Search music library for song
    for i, index in enumerate(music_index["origin"]):
      if index == url:
        return music_index["path"][i]
  
  def download_song(self, url):
    """Downloads and returns new song name"""
    yt_request = pytube.YouTube(url)
    song_uuid = str(uuid.uuid4()) + '.webm'
    
    audio_qualities = yt_request.streams.filter().all()
    best_audio_quality = yt_request.streams.get_by_itag(251)
    best_audio_quality.download(filename=song_uuid,
                        output_path=self.library_path+'/indexed')
    return {"id": song_uuid, 
            "path": os.path.join(os.getcwd(), song_uuid),
            "origin": url}


def setup(bot):
  bot.add_cog(Core_V1(bot))
  