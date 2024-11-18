import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import requests

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
api_url = "API"

class ZitatModal(discord.ui.Modal, title='Neues Zitat'):
    name = discord.ui.TextInput(label='Name', placeholder='Name der Person')
    zitat = discord.ui.TextInput(label='Zitat', placeholder='Das Zitat')

    async def on_submit(self, interaction: discord.Interaction):
        await add_new_quote(self.name.value, self.zitat.value)
        await interaction.response.send_message(f"Zitat hinzugefügt!", ephemeral=True)

class ZitatButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Zitat hinzufügen", style=discord.ButtonStyle.primary)
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ZitatModal())

# Variable zum Speichern der Nachricht mit dem Button
zitat_message = None

async def update_zitat_button_message(channel):
    """Sendet eine neue Nachricht mit dem Button und fügt optisch eine Trennung hinzu."""
    global zitat_message
    if zitat_message:  # Prüfen, ob es eine alte Nachricht gibt
        try:
            await zitat_message.delete()
        except discord.NotFound:
            pass  # Nachricht wurde schon gelöscht

    async for message in channel.history(limit=5):  # Limit auf 10, um unnötig viele Nachrichten zu prüfen
        if message.content == "\u200B":  # Zero Width Space als Trenner
            await message.delete()

    # Optische Trennung einfügen
    await channel.send("\u200B")
    await channel.send("\u200B")
    await channel.send("\u200B")
    await channel.send("\u200B")  # Optischer Trenner
    
    # Neue Nachricht mit dem Button senden
    zitat_message = await channel.send("Klicke hier, um ein neues Zitat hinzuzufügen:", view=ZitatButton())


@bot.event
async def on_ready():
    global data
    await bot.tree.sync()
    data = fetch_data_from_api()
    bot.loop.create_task(check_for_new_quote())
    print(f'Logged in as {bot.user.name}')

    # Nachricht mit dem Button initial senden
    channel = bot.get_channel("Channel ID")  # Kanal-ID
    if channel:
        await update_zitat_button_message(channel)

@bot.tree.command(name="zitat", description="Füge ein neues Zitat hinzu")
async def zitat(interaction: discord.Interaction):
    """Füge ein neues Zitat hinzu"""
    await interaction.response.send_modal(ZitatModal())

async def add_new_quote(name, quote):
    global data
    try:
        response = requests.post(api_url, json={"name": name, "msg": quote})
        if response.status_code == 200:
            print("Zitat erfolgreich hinzugefügt!")
            fetch_data_from_api() 
        else:
            print(response.status_code)
    except ValueError:
        print("Falsches Format.")
    return response.status_code

@bot.event
async def on_message(msg):
    global data, zitat_message
    if msg.author == bot.user:
        return

    if msg.channel.id == "Channel ID":
        await delete_last_messages(msg.channel)

        # Aktualisiere die Nachricht mit dem Button
        channel = bot.get_channel("Channel ID")  # Kanal-ID
        if channel:
            await update_zitat_button_message(channel)

    if msg.channel.id == 870752551828611102:
        if msg.content.startswith('/play') or msg.content.startswith('!play') or (
            msg.author.name == 'Chip' and msg.author.discriminator == '4145'):
            await delete_last_messages(msg.channel)

async def delete_last_messages(channel):
    """Löscht die letzten Nachrichten in einem Kanal."""
    async for previous_msg in channel.history(limit=1):
        await previous_msg.delete()

def fetch_data_from_api():
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Fehler beim Abrufen der Daten. Status-Code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Fehler beim Abrufen der Daten: {e}")
        return None

def format_data(data):
    newest_quote = max(data['data'], key=lambda x: x['id'])
    formatted_message = f'```fix\n{newest_quote["name"]}: "{newest_quote["msg"]}" #{newest_quote["id"]}```'
    return formatted_message

def format_alldata(data):
    formatted_message = "Neueste Zitate:\n"
    for zitat in data['data']:
        formatted_message += f"`{zitat['name']}: {zitat['msg']} #{zitat['id']}`\n"
    return formatted_message

async def check_for_new_quote():
    global data, zitat_message
    while not bot.is_closed():
        await asyncio.sleep(5)  
        if data is not None:
            new_data = fetch_data_from_api()
            if new_data != data:
                channel = bot.get_channel("Channel ID") 
                if channel:
                    await channel.send(format_data(new_data))

                    # Aktualisiere die Nachricht mit dem Button
                    await update_zitat_button_message(channel)

                data = new_data

bot.run('TOKEN')
