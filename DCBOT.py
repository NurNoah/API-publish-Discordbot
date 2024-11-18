import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import requests

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
api_url = "api"

class ZitatModal(discord.ui.Modal, title='Neues Zitat'):
    name = discord.ui.TextInput(label='Name', placeholder='Name der Person')
    zitat = discord.ui.TextInput(label='Zitat', placeholder='Das Zitat', style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        await add_new_quote(self.name.value, self.zitat.value)
        await interaction.response.send_message(f"Zitat hinzugefügt!", ephemeral=True)

class ZitatButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) 

    @discord.ui.button(label="Zitat hinzufügen", style=discord.ButtonStyle.primary)
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ZitatModal())


@bot.event
async def on_ready():
    global data, zitat_message
    await bot.tree.sync()
    data = fetch_data_from_api()
    bot.loop.create_task(check_for_new_quote()) 
    print(f'Logged in as {bot.user.name}')
    
    channel = bot.get_channel("channel id")  # Kanal-ID für die Nachricht mit Button
    if channel:
        zitat_message = await channel.send("Klicke hier, um ein neues Zitat hinzuzufügen:", view=ZitatButton())

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
        await print(f"Falsches Format.")
    return response.status_code

@bot.event
async def on_message(msg):
    global data
    if msg.author == bot.user:
        return
    if msg.channel.id == "channel id":
        await delete_last_messages(msg.channel)
    if msg.channel.id == "channel id":
        if msg.content.startswith('/play') or msg.content.startswith('!play') or (
            msg.author.name == 'Chip' and msg.author.discriminator == '4145'):
            await delete_last_messages(msg.channel)

async def delete_last_messages(channel):
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
    global data
    while not bot.is_closed():
        await asyncio.sleep(5)  
        if data is not None:
            new_data = fetch_data_from_api()
            if new_data != data:
                channel = bot.get_channel("channel id") 
                if channel:
                    await channel.send(format_data(new_data))
                data = new_data

bot.run('token')