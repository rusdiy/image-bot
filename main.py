import discord
from discord.ext import commands
from meme_overlay import MemeTextOverlay
from rps import RPSLaunchView, RPSChoice
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


@bot.command(name="rps")
async def rps(ctx: commands.Context, opponent: discord.Member):
    if not opponent:
        await ctx.send("Please mention an opponent.")
        return
    await ctx.message.delete()
    if opponent.bot or ctx.author == opponent:
        raise commands.BadArgument(
            "You cannot play against a bot or yourself."
        )

    description = f"{ctx.author.mention}: ❓ vs {opponent.mention}: ❓"
    embed = discord.Embed(
        title="Rock Paper Scissors",
        description=description,
        color=discord.Color.blurple()
    )
    choice_view = RPSChoice(ctx, ctx.author, opponent, 0)
    lauch_view = RPSLaunchView(ctx, ctx.author, opponent, 0, choice_view)
    content = (
        f"{ctx.author.mention} has challenged {opponent.mention}\n"
        "Click the button below to accept the challenge!"
    )
    msg = await ctx.send(content=content, embed=embed, view=lauch_view)
    choice_view.message_id = msg.id
    lauch_view.message_id = msg.id


@rps.error
async def rps_error(ctx: commands.Context, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please mention an opponent.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")


if __name__ == "__main__":
    bot.run(TOKEN)
