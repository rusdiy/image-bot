import discord
from discord.ext import commands
from discord.ui import View, Button, button


class RPSChoice(View):
    def __init__(
        self, ctx: commands.Context,
        player1: discord.Member,
        player2: discord.Member,
        message_id: int
    ):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.player1 = player1
        self.player2 = player2
        self.message_id = message_id
        self.choices = {}

    async def interaction_check(
            self, interaction: discord.Interaction) -> bool:
        return interaction.user.id in (self.player1.id, self.player2.id)

    async def on_timeout(self):
        msg = await self.ctx.channel.fetch_message(self.message_id)
        await msg.edit(content="⏰ Game timed out.", view=None)

    async def button_click(
        self,
        interaction: discord.Interaction,
        choice: str,
        emoji: str
    ):
        self.choices[interaction.user.id] = choice
        await interaction.response.edit_message(
            content=f"You chose {emoji} **{choice.capitalize()}**!",
            delete_after=2,
            view=None
        )

        msg = await self.ctx.channel.fetch_message(self.message_id)
        embed = msg.embeds[0]
        content = embed.description

        if interaction.user.id == self.player1.id:
            content = content.replace(
                f"{self.player1.mention}: ❓", f"{self.player1.mention}: ✅")
        else:
            content = content.replace(
                f"{self.player2.mention}: ❓", f"{self.player2.mention}: ✅")
        embed.description = content
        await msg.edit(embed=embed)
        if len(self.choices) == 2:
            await self.resolve_game()

    async def resolve_game(self):
        p1_choice = self.choices[self.player1.id]
        p2_choice = self.choices[self.player2.id]

        emoji_map = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        msg = await self.ctx.channel.fetch_message(self.message_id)

        result_text = (
            f"{self.player1.mention} {emoji_map[p1_choice]} vs "
            f"{emoji_map[p2_choice]} {self.player2.mention}\n\n"
            f"## {self.get_result(p1_choice, p2_choice)}"
        )
        embed = discord.Embed(
            title="Rock Paper Scissors Result",
            description=result_text,
            color=discord.Color.blurple()
        )
        await msg.channel.send(embed=embed)
        await msg.delete()
        self.stop()

    def get_result(self, c1: str, c2: str):
        if c1 == c2:
            return "It's a draw! 🤝"

        beats = {
            "rock": "scissors",
            "scissors": "paper",
            "paper": "rock"
        }

        if beats[c1] == c2:
            return f"{self.player1.mention} wins!"
        else:
            return f"{self.player2.mention} wins!"

    @button(label="Rock", style=discord.ButtonStyle.secondary, emoji="🪨")
    async def rock(self, interaction: discord.Interaction, button: Button):
        await self.button_click(interaction, "rock", "🪨")

    @button(label="Paper", style=discord.ButtonStyle.secondary, emoji="📄")
    async def paper(self, interaction: discord.Interaction, button: Button):
        await self.button_click(interaction, "paper", "📄")

    @button(label="Scissors", style=discord.ButtonStyle.secondary, emoji="✂️")
    async def scissors(self, interaction: discord.Interaction, button: Button):
        await self.button_click(interaction, "scissors", "✂️")


class RPSLaunchView(View):
    def __init__(
        self,
        ctx: commands.Context,
        player1: discord.Member,
        player2: discord.Member,
        message_id: int,
        choice_view: RPSChoice = None
    ):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.player1 = player1
        self.player2 = player2
        self.message_id = message_id
        self.choice_view = choice_view

    async def interaction_check(
            self, interaction: discord.Interaction) -> bool:
        return interaction.user.id in (self.player1.id, self.player2.id)

    @button(label="Play", style=discord.ButtonStyle.primary, emoji="🎮")
    async def play_button(
        self, interaction: discord.Interaction, button: Button
    ):
        await interaction.response.send_message(
            "Choose your move:",
            ephemeral=True,
            view=self.choice_view
        )

    @button(label="Deny", style=discord.ButtonStyle.grey, emoji="❌")
    async def cancel_button(
        self, interaction: discord.Interaction, button: Button
    ):
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} has cancelled the game.",
            delete_after=5,
            view=None,
            embed=None
        )
        self.stop()

    async def on_timeout(self):
        msg = await self.ctx.channel.fetch_message(self.message_id)
        await msg.edit(content="⏰ Game timed out.", view=None)
