# https://www.youtube.com/watch?v=YD_N6Ffoojw
# https://www.youtube.com/watch?v=26Sj5hJFqUs&t=21s
# https://www.youtube.com/watch?v=O7SI9uLuN_8

# discord bot token loading and initialisation
from typing import Optional
import discord
from discord.ext import commands
#from discord import app_commands
#from discord.ui import Button, View
import logging
from dotenv import load_dotenv
import json
import os

import random

import webserver
import requests

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN", None)
JSONBIN_API_KEY = os.getenv("JSONBIN_API_KEY")
JSONBIN_ENTITIES = os.getenv("JSONBIN_ENTITIES")
JSONBIN_BATTLEFIELD = os.getenv("JSONBIN_BATTLEFIELD")
# Note: client.run(token) only works if the following is included:
if TOKEN is None:
    raise RuntimeError("DISCORD_TOKEN not found in .env")
if not JSONBIN_API_KEY or not JSONBIN_ENTITIES or not JSONBIN_BATTLEFIELD:
    raise RuntimeError("jsonbin value not found in .env")

# basic logging
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w') # 'w' stands for write mode

# bot intents
intents = discord.Intents.default()

# specify manual intents (must be done in Discord developer page and in code)
# "Every single permission will be included in one of these intents"
# "A Primer to Gateway Intents"
intents.message_content = True
intents.members = True

client = commands.Bot(command_prefix="!", intents=intents)
tree = client.tree

#GUILD_ID = discord.Object(id=1379996881362485328)

# @client.tree.command(name="hello", description="Say hello!", guild=GUILD_ID)
# async def sayHello(interaction: discord.Interaction):
#     await interaction.response.send_message("Hi there!")

#token = os.getenv("DISCORD_TOKEN")

JSONBIN_BASE_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_ENTITIES}"
HEADERS = {
    "X-Master-Key": JSONBIN_API_KEY,
    "Content-Type": "application/json"
}

JSONBIN_BATTLE_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_BATTLEFIELD}"
HEADERS = {
    "X-Master-Key": JSONBIN_API_KEY,
    "Content-Type": "application/json"
}

user_entities = {}
battlefield_entities = {}

def load_entities_from_jsonbin():
    try:
        response = requests.get(JSONBIN_BASE_URL + "/latest", headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        # The actual data is inside data['record']
        entities = data.get("record", {})
        # convert keys back to int (json keys are strings)
        return {int(k): v for k, v in entities.items()}
    except Exception as e:
        print(f"Error loading data from jsonbin: {e}")
        return {}
    
# def load_saved_output_channel():
#     try:
#         response = requests.get(JSONBIN_BASE_URL + "/latest", headers=HEADERS)
#         response.raise_for_status()
#         data = response.json()
#         return data.get("record", {})
#     except Exception as e:
#         print(f"Error loading data from jsonbin: {e}")
#         return {}

def load_battlefield():
    try:
        response = requests.get(JSONBIN_BATTLE_URL + "/latest", headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        # The actual data is inside data['record']
        entities = data.get("record", {})
        # convert keys back to int (json keys are strings)
        return {int(k): v for k, v in entities.items()}
    except Exception as e:
        print(f"Error loading data from jsonbin: {e}")
        return {}


# Load on startup
user_entities = load_entities_from_jsonbin()
battlefield = load_battlefield()

# channel_id = load_saved_output_channel()

def save_data_to_jsonbin():
    try:
        # jsonbin expects the whole JSON object
        response = requests.put(JSONBIN_BASE_URL, headers=HEADERS, json=user_entities)
        response.raise_for_status()
    except Exception as e:
        print(f"Error saving data to jsonbin: {e}")

def save_battlefield_to_jsonbin():
    try:
        # jsonbin expects the whole JSON object
        response = requests.put(JSONBIN_BATTLE_URL, headers=HEADERS, json=battlefield)
        response.raise_for_status()
    except Exception as e:
        print(f"Error saving data to jsonbin: {e}")

# In-memory storage dictionary: user_id -> data dict
# user_entities = {}

# DATA_FILE = "user_entities.json"
# DATA_FILE2 = "output_channel.json"

# # Load data on startup
# if os.path.exists(DATA_FILE):
#     try:
#         with open(DATA_FILE, "r") as f:
#             user_entities = json.load(f)
#             # convert keys back to int
#             user_entities = {int(k): v for k, v in user_entities.items()}
#     except json.JSONDecodeError:
#         user_entities = {}
# else:
#     user_entities = {}

# # Save data function
# def save_data():
#     with open(DATA_FILE, "w") as f:
#         json.dump(user_entities, f)

@client.event
async def on_ready():
    print(f"logged on as {client.user}")
    await client.tree.sync()

@tree.command(name='ping', description="sdfjhfkds")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong!")

#_______

@tree.command(name="get_information_format", description="See how create_entity formats input")
async def get_format(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"*name*"
        f"[*emoji*] "
        f"*hp*hp\n"
        f"> *atk & description*\n"
        f"(*description*)"
    )

@tree.command(name="create_entity", description="Create an entity")
@discord.app_commands.describe(
    name="Entity name",
    icon="Entity icon/emoji",
    hp="Entity health",
    atk="Entity attacks and damage",
    desc="Entity description"
)
async def create_entity(interaction: discord.Interaction, name: str, icon: str, hp: int, atk: str, desc: str):
    user_list = user_entities.setdefault(interaction.user.id, [])
    for e in user_list:
        if e['name'].lower() == name.lower():
            await interaction.response.send_message("You can not have two entities with the same name.")
            return
    entity = {
        "name": name,
        "icon": icon,
        "hp": hp,
        "atk": atk,
        "desc": desc
    }
    user_list = user_entities.setdefault(interaction.user.id, [])
    user_list.append(entity)
    await interaction.response.send_message(f"Entity '{name}' saved! You now have {len(user_list)} entities.")
    #save_data()
    save_data_to_jsonbin()

#-------------

@tree.command(name="list_entities", description="List all saved entities")
async def list_entities(interaction: discord.Interaction):
    entities = user_entities.get(interaction.user.id)
    if not entities:
        await interaction.response.send_message("You have no saved entities yet. Use /create_entity to add one.", ephemeral=True)
        return

    response = ""
    for i, e in enumerate(entities, start=1):
        response += f"{i}.\t{e['name']}[{e['icon']}]\n"  # Only names here
    await interaction.response.send_message(response, ephemeral=True)

#-------------

@tree.command(name="get_entity", description="Get an entity by name")
@discord.app_commands.describe(name="The name of the entity to retrieve")
async def get_entity(interaction: discord.Interaction, name: str):
    entities = user_entities.get(interaction.user.id)
    if not entities:
        await interaction.response.send_message("You have no saved entities yet.", ephemeral=True)
        return

    # Search for entity with matching name (case insensitive)
    entity = next((e for e in entities if e["name"].lower() == name.lower()), None)
    if not entity:
        await interaction.response.send_message(f"No entity found with name '{name}'.", ephemeral=True)
        return

    await interaction.response.send_message(
        f"{entity['name']}"
        f"[{entity['icon']}] "
        f"{entity['hp']}hp\n"
        f"> {entity['atk']}\n"
        f"({entity['desc']})"
    )

#-------------

@client.tree.command(name="modify_entity", description="Modify an existing entity")
@discord.app_commands.describe(
    name="Name of the entity to edit",
    new_name="New name (optional)",
    new_icon="New icon (optional)",
    new_hp="New health value (optional)",
    new_atk="New attack info (optional)",
    new_desc="New description (optional)"
)
async def modify_entity(
    interaction: discord.Interaction,
    name: str,
    new_name: str = "",
    new_icon: str = "",
    new_hp: Optional[int] = None,
    new_atk: str = "",
    new_desc: str = ""
):
    entities = user_entities.get(interaction.user.id)
    if not entities:
        await interaction.response.send_message("You have no saved entities.", ephemeral=True)
        return

    entity = next((e for e in entities if e["name"].lower() == name.lower()), None)
    if not entity:
        await interaction.response.send_message(f"No entity found with name '{name}'.", ephemeral=True)
        return

    updates = []

    if new_name:
        updates.append(f"Name changed from `{entity['name']}` to `{new_name}`")
        entity["name"] = new_name
    if new_icon:
        updates.append(f"Icon changed from `{entity['icon']}` to `{new_icon}`")
        entity["icon"] = new_icon
    if new_hp is not None:
        updates.append(f"HP changed from `{entity['hp']}` to `{new_hp}`")
        entity["hp"] = new_hp
    if new_atk:
        updates.append(f"ATK changed from `{entity['atk']}` to `{new_atk}`")
        entity["atk"] = new_atk
    if new_desc:
        updates.append(f"Description changed from `{entity['desc']}` to `{new_desc}`")
        entity["desc"] = new_desc

    if not updates:
        await interaction.response.send_message("No updates provided.", ephemeral=True)
        return

    #save_data()
    save_data_to_jsonbin()
    await interaction.response.send_message("✅ Entity updated:\n" + "\n".join(updates))

# -------------

@client.tree.command(name="delete_entity", description="Delete one of your saved entities")
@discord.app_commands.describe(
    name="Name of the entity to delete",
    confirm="Confirm the name of the entity"
)
async def delete_entity(interaction: discord.Interaction, name: str, confirm: str):
    entities = user_entities.get(interaction.user.id)
    if not entities:
        await interaction.response.send_message("You have no saved entities.", ephemeral=True)
        return

    # Find the entity by exact name
    entity = next((e for e in entities if e["name"] == name), None)

    if not entity:
        await interaction.response.send_message(f"No entity found with name '{name}'.", ephemeral=True)
        return

    if name == confirm:
        entities.remove(entity)
    else:
        await interaction.response.send_message(f"Names do not match; no entity has been deleted.", ephemeral=True)
        return

    await interaction.response.send_message(f"Entity '{name}' has been deleted.", ephemeral=True)
    #save_data()
    save_data_to_jsonbin()

# -----------

@client.tree.command(name="clear_entire_entity_list", description="Delete ALL entities from the list")
@discord.app_commands.describe(
    confirm='To delete all entities, input "DELETE ALL"'
)
async def delete_all(interaction: discord.Interaction, confirm: str):
    if confirm == "DELETE ALL":
        entities = user_entities.get(interaction.user.id)
        if not entities:
            await interaction.response.send_message("You have no saved entities yet. Use /create_entity to add one.", ephemeral=True)
            return

        if interaction.user.id in user_entities:
            del user_entities[interaction.user.id]
            await interaction.response.send_message("All entities have been deleted.", ephemeral=True)
            #save_data()
            save_data_to_jsonbin()

    else:
        await interaction.response.send_message("Input does not match; entities have not been deleted.", ephemeral=True)

#--------------------

@client.tree.command(name="dice_roll", description="Roll a dice")
@discord.app_commands.describe(
    dice_type="The dice type/max number to roll",
    num_dice="Number of dice to roll"
)
async def dice_roll(interaction: discord.Interaction, dice_type: int, num_dice: int = 1):
    results = []
    for _ in range(num_dice):
        roll = random.randint(1, dice_type)
        results.append(roll)

    # Convert rolls to string, separated by commas
    rolls_str = " ".join(f"`{r}`" for r in results)
    await interaction.response.send_message(f"You rolled {num_dice}d{dice_type}: {rolls_str}")

#---------------

@client.tree.command(name="load_entity_into_battle", description="Load an entity onto the battlefield")
@discord.app_commands.describe(
    name="Load an entity from name",
    current_hp="The entity's current health"
)
async def load_entity(interaction: discord.Interaction, name: str, current_hp: Optional[int] = None):
    user_id = interaction.user.id
    entities = user_entities.get(user_id)

    if not entities:
        await interaction.response.send_message("You have no saved entities.", ephemeral=True)
        return

    # Find the entity by exact name
    entity = next((e for e in entities if e["name"] == name), None)

    if not entity:
        await interaction.response.send_message(f"No entity found with name '{name}'.", ephemeral=True)
        return

    # Use the provided current_hp or the entity's default hp
    battle_entity = {
        "name": entity["name"],
        "icon": entity["icon"],
        "hp": current_hp if current_hp is not None else entity["hp"]
    }

    dupe_count = 1

    for i, e in enumerate(entities, start=1):
        if battle_entity['name'] == e['name']:
            dupe_count += 0

    if dupe_count != 0:
        battle_entity["name"] += f" ({dupe_count})"

    # Add to battlefield list (e.g., per user or globally)
    if user_id not in battlefield_entities:
        battlefield_entities[user_id] = []
    battlefield_entities[user_id].append(battle_entity)

    await interaction.response.send_message(
        f"Entity **{battle_entity['name']}** loaded into battle with {battle_entity['hp']} HP!",
        ephemeral=True
    )
    
    # @tree.command(name="create_entity", description="Create an entity")
    # @discord.app_commands.describe(
        # name="Entity name",
        # icon="Entity icon/emoji",
        # hp="Entity health",
        # atk="Entity attacks and damage",
        # desc="Entity description"
    # )
    # async def create_entity(interaction: discord.Interaction, name: str, icon: str, hp: int, atk: str, desc: str):
    # user_list = user_entities.setdefault(interaction.user.id, [])
    # for e in user_list:
    #     if e['name'].lower() == name.lower():
    #         await interaction.response.send_message("You can not have two entities with the same name.")
    #         return
    # entity = {
    #     "name": name,
    #     "icon": icon,
    #     "hp": hp,
    #     "atk": atk,
    #     "desc": desc
    # }
    # user_list = user_entities.setdefault(interaction.user.id, [])
    # user_list.append(entity)
    # await interaction.response.send_message(f"Entity '{name}' saved! You now have {len(user_list)} entities.")
    # #save_data()
    # save_data_to_jsonbin()
    
#-------------

# @tree.command(name="get_entity", description="Get an entity by name")
# @discord.app_commands.describe(name="The name of the entity to retrieve")
# async def get_entity(interaction: discord.Interaction, name: str):
#     entities = user_entities.get(interaction.user.id)
#     if not entities:
#         await interaction.response.send_message("You have no saved entities yet.", ephemeral=True)
#         return

#     # Search for entity with matching name (case insensitive)
#     entity = next((e for e in entities if e["name"].lower() == name.lower()), None)
#     if not entity:
#         await interaction.response.send_message(f"No entity found with name '{name}'.", ephemeral=True)
#         return

#     await interaction.response.send_message(
#         f"{entity['name']}"
#         f"[{entity['icon']}] "
#         f"{entity['hp']}hp\n"
#         f"> {entity['atk']}\n"
#         f"({entity['desc']})"
#     )

webserver.keep_alive()
client.run(TOKEN)




#old-----

# load_dotenv()
# token = os.getenv("DISCORD_TOKEN")

# # basic logging
# handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w') # 'w' stands for write mode

# # bot intents
# intents = discord.Intents.default()

# # specify manual intents (must be done in Discord developer page and in code)
# # "Every single permission will be included in one of these intents"
# # "A Primer to Gateway Intents"
# intents.message_content = True
# intents.members = True

# # create a Discord bot/entity
# bot = commands.Bot(command_prefix='!', intents=intents)

# # responding to events
# @bot.event
# async def on_ready():
#     print(f"We are read to go in, {bot.user.name}") # f string

# when a new member joins
# @bot.event
# async def on_member_join(member):
#     await member.send(f"Welcome to the server {member.name}") # sends a dm

# on message
# @bot.event
# async def on_message(message):
#     # we do not want the bot replying to its own message
#     if message.author == bot.user:
#         return
#     if "shit" in message.content.lower():
#         await message.delete()
#         await message.channel.send(f"{message.author.mention} don't use that word!") # tag/pings member
#     await bot.process_commands(message) # continues handling messages

# @bot.command()
# # triggers with "!hello"
# # 'ctx' means context
# async def hello(ctx):
#     await ctx.send(f"Hello {ctx.author.mention}!")

# bot.run(token, log_handler=handler, log_level=logging.DEBUG)
