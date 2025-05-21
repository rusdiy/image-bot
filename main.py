import discord
from discord.ext import commands
from meme_overlay import MemeTextOverlay
from dotenv import load_dotenv
import os


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
bot = commands.Bot(
    command_prefix=";;",
    intents=discord.Intents.all(),
    help_command=None
)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} - {bot.user.id}")
    print("------")


@bot.command()
async def meme(ctx: commands.Context, image_url: str, *, text: str):
    """Create a meme with the given image URL and text."""
    async with ctx.typing():
        try:
            await ctx.message.delete()
            overlay = MemeTextOverlay()
            image_url = image_url.strip()
            if not image_url.startswith("http"):
                await ctx.send("Please provide a valid image URL.")
                return
            if not text:
                await ctx.send("Please provide text for the meme.")
                return
            # Create the meme
            buffer, filename = overlay.apply_to_image(image_url, text)
            await ctx.send(file=discord.File(fp=buffer, filename=filename))
        except Exception as e:
            await ctx.send(f"Error: {str(e)}")


if __name__ == "__main__":
    bot.run(TOKEN)
