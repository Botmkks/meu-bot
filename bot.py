import discord
from discord import app_commands, ui
from discord.ext import commands
import os

# --- CONFIGURAÇÕES DE IDs ---
# Recomendação
ID_CARGO_PERMISSAO_REC = 1473313398602072278
ID_CARGO_STAFF_REC = 1473311965240627264
ID_CANAL_RECOMENDACOES = 1473310123198906411

# Ticket
ID_CARGO_STAFF_TICKET = 1473313724830843113

# --- SISTEMA DE CONTADOR DE TICKETS ---
def get_next_ticket_number():
    if not os.path.exists("counter.txt"):
        with open("counter.txt", "w") as f:
            f.write("1")
        return 1
    with open("counter.txt", "r") as f:
        number = int(f.read())
    with open("counter.txt", "w") as f:
        f.write(str(number + 1))
    return number

# --- CLASSES DO SISTEMA DE RECOMENDAÇÃO ---
class RecommendActions(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def update_embed(self, interaction, title, color):
        role_staff = interaction.guild.get_role(ID_CARGO_STAFF_REC)
        if role_staff not in interaction.user.roles:
            return await interaction.response.send_message(
                "Você não tem permissão de Staff!", ephemeral=True
            )

        old_embed = interaction.message.embeds[0]
        new_embed = discord.Embed(title=title, color=color)

        for field in old_embed.fields:
            new_embed.add_field(
                name=field.name,
                value=field.value,
                inline=field.inline
            )

        await interaction.message.edit(embed=new_embed, view=None)
        await interaction.response.send_message(
            f"Ação realizada por {interaction.user.mention}"
        )

    @ui.button(label="ACEITAR", style=discord.ButtonStyle.success, emoji="⭐", custom_id="acc_rec")
    async def accept(self, interaction: discord.Interaction, button: ui.Button):
        await self.update_embed(
            interaction,
            "✅ Recomendação Aceita",
            discord.Color.green()
        )

    @ui.button(label="RECUSAR", style=discord.ButtonStyle.danger, emoji="❌", custom_id="rej_rec")
    async def reject(self, interaction: discord.Interaction, button: ui.Button):
        await self.update_embed(
            interaction,
            "❌ Recomendação Recusada",
            discord.Color.greyple()
        )

# --- CLASSES DO SISTEMA DE TICKET ---
class TicketControl(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Fechar Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket")
    async def close_button(self, interaction: discord.Interaction, button: ui.Button):
        role_staff = interaction.guild.get_role(ID_CARGO_STAFF_TICKET)
        if role_staff not in interaction.user.roles:
            return await interaction.response.send_message(
                "Apenas a Staff pode fechar este ticket!",
                ephemeral=True
            )

        await interaction.response.send_message("Deletando canal...")
        await interaction.channel.delete()

class TicketLauncher(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Abrir Ticket", style=discord.ButtonStyle.primary, emoji="📩", custom_id="open_ticket")
    async def open_button(self, interaction: discord.Interaction, button: ui.Button):
        guild = interaction.guild
        user = interaction.user
        num = get_next_ticket_number()

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.get_role(ID_CARGO_STAFF_TICKET):
                discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{num}",
            overwrites=overwrites
        )

        await channel.send(
            content=f"Bem-Vindo {user.mention}, Declare seu problema ou sua dúvida",
            view=TicketControl()
        )

        await interaction.response.send_message(
            f"Ticket criado: {channel.mention}",
            ephemeral=True
        )

# --- BOT CORE ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(RecommendActions())
        self.add_view(TicketLauncher())
        self.add_view(TicketControl())
        await self.tree.sync()
        print("Sistemas Sincronizados!")

bot = MyBot()

# --- COMANDO RECOMMEND (SLASH) ---
@bot.tree.command(name="recommend", description="Recomende uma pessoa para a Concept.")
@app_commands.describe(
    roblox="Usuário do Roblox",
    discord_u="Usuário do Discord",
    desc="Descrição"
)
async def recommend(
    interaction: discord.Interaction,
    roblox: str,
    discord_u: str,
    desc: str
):
    role_permissao = interaction.guild.get_role(ID_CARGO_PERMISSAO_REC)
    if role_permissao not in interaction.user.roles:
        return await interaction.response.send_message(
            "Você não tem permissão para recommend",
            ephemeral=True
        )

    canal = (
        bot.get_channel(ID_CANAL_RECOMENDACOES)
        or await bot.fetch_channel(ID_CANAL_RECOMENDACOES)
    )

    embed = discord.Embed(
        title="⭐ Nova Recomendação",
        color=0xFF0000
    )

    embed.add_field(
        name="👤 Jogador Recomendado",
        value=f"**Roblox:** {roblox}\n**Discord:** {discord_u}",
        inline=False
    )

    embed.add_field(
        name="💼 Recomendado por:",
        value=f"**Discord:** {interaction.user.mention}",
        inline=False
    )

    embed.add_field(
        name="🗒️ Descrição:",
        value=desc,
        inline=False
    )

    await canal.send(embed=embed, view=RecommendActions())
    await interaction.response.send_message(
        "✅ Recomendação enviada!",
        ephemeral=True
    )

# --- COMANDO TICKET ---
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx):
    embed = discord.Embed(
        title="🎫 Central de Atendimento",
        description="Clique no botão abaixo para abrir um ticket.",
        color=discord.Color.red()
    )

    await ctx.send(embed=embed, view=TicketLauncher())
    await ctx.message.delete()

# --- TOKEN ---
bot.run(os.getenv("TOKEN"))
