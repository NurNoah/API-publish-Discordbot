import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import requests

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
api_url = "http://localhost:8000/api/zitate"

@bot.event
async def on_ready():
    global data
    await bot.tree.sync()
    data = fetch_data_from_api()
    bot.loop.create_task(check_for_new_quote()) 
    print(f'Logged in as {bot.user.name}')

@bot.tree.command(name="zitat", description="Füge ein neues Zitat hinzu")
@app_commands.describe(name = "Name der Person die das Zitat gesagt hat")
@app_commands.describe(zitat = "Das gesprochene Zitat")
async def say(interaction: discord.Interaction, name:str, zitat:str):
    await interaction.response.send_message(f"Erfolgreich", ephemeral=True)
    await add_new_quote(name, zitat)
   

async def add_new_quote(name, quote):
    global data
    try:
        response = requests.post(api_url, json={"name": name, "msg": quote})
        if response.status_code == 200:
            await print("Zitat erfolgreich hinzugefügt!")
            data = fetch_data_from_api()  # Aktualisieren der Daten
        else:
            print(response.status_code)
    except ValueError:
        await print(f"Falsches Format. Verwenden Sie: /zitat [Name] [Zitat]")
    return response.status_code

@bot.event
async def on_message(msg):
    global data
    if msg.author == bot.user:
        return
    elif msg.channel.id == 870752551828611102:
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
                channel = bot.get_channel(938918163448492062) 
                if channel:
                    await channel.send(format_data(new_data))
                data = new_data

bot.run('DCTOKEN')
