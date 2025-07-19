import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Modal, TextInput
import json
import os
from dotenv import load_dotenv
from typing import List

# Load .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = discord.Object(id=int(os.getenv("GUILD_ID")))

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!", "?", "/"), intents=intents)
tree = bot.tree

# JSON persistence
SETTINGS_FILE = "settings.json"
PROFILE_FILE = "embed_profiles.json"

if not os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "w") as f:
        json.dump({}, f)

def load_settings():
    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)

def save_settings():
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

settings = load_settings()

def load_embed_profiles():
    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            profiles = {}
            for name, embed_dict in raw_data.items():
                profiles[name] = discord.Embed.from_dict(embed_dict)
            return profiles
    except (FileNotFoundError, json.JSONDecodeError):
        return {"default": discord.Embed(title="Default Title", description="Default Description", color=discord.Color.blue())}

def save_embed_profiles():
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump({name: embed.to_dict() for name, embed in embed_profiles.items()}, f, indent=4)

embed_profiles = load_embed_profiles()

class EmbedModal(Modal):
    def __init__(self, name):
        super().__init__(title=f"Edit Embed: {name}")
        self.name = name
        self.title_input = TextInput(label="Title", placeholder="Enter a title")
        self.description_input = TextInput(label="Description", placeholder="Enter a description", style=discord.TextStyle.paragraph)
        self.add_item(self.title_input)
        self.add_item(self.description_input)

    async def on_submit(self, interaction: discord.Interaction):
        embed_profiles[self.name].title = self.title_input.value
        embed_profiles[self.name].description = self.description_input.value
        save_embed_profiles()
        await interaction.response.send_message("Embed updated successfully!", ephemeral=True)

class AuthorModal(Modal):
    def __init__(self, name):
        super().__init__(title=f"Edit Author: {name}")
        self.name = name
        self.name_input = TextInput(label="Author Name")
        self.icon_url_input = TextInput(label="Author Icon URL (Optional)", required=False)
        self.add_item(self.name_input)
        self.add_item(self.icon_url_input)

    async def on_submit(self, interaction: discord.Interaction):
        embed_data = embed_profiles[self.name]
        icon_url = self.icon_url_input.value or None
        embed_data.set_author(name=self.name_input.value, icon_url=icon_url)
        save_embed_profiles()
        await interaction.response.send_message("Author updated!", ephemeral=True)

class ImageModal(Modal):
    def __init__(self, name):
        super().__init__(title=f"Edit Images: {name}")
        self.name = name
        self.thumbnail_input = TextInput(label="Thumbnail URL")
        self.image_input = TextInput(label="Main Image URL")
        self.add_item(self.thumbnail_input)
        self.add_item(self.image_input)

    async def on_submit(self, interaction: discord.Interaction):
        embed_data = embed_profiles[self.name]
        embed_data.set_thumbnail(url=self.thumbnail_input.value or None)
        embed_data.set_image(url=self.image_input.value or None)
        save_embed_profiles()
        await interaction.response.send_message("Images updated!", ephemeral=True)

class ColorModal(Modal):
    def __init__(self, name):
        super().__init__(title=f"Edit Color: {name}")
        self.name = name
        self.color_input = TextInput(label="Hex Color Code", placeholder="#cfaf00")
        self.add_item(self.color_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            hex_code = self.color_input.value.lstrip("#")
            color = discord.Color(int(hex_code, 16))
            embed_profiles[self.name].color = color
            save_embed_profiles()
            await interaction.response.send_message("Color updated!", ephemeral=True)
        except Exception:
            await interaction.response.send_message("Invalid color code!", ephemeral=True)

class EmbedEditorView(View):
    def __init__(self, name):
        super().__init__()
        self.name = name

    @discord.ui.button(label="Edit Title & Description", style=discord.ButtonStyle.primary)
    async def edit_main(self, interaction, button):
        await interaction.response.send_modal(EmbedModal(self.name))

    @discord.ui.button(label="Edit Author", style=discord.ButtonStyle.secondary)
    async def edit_author(self, interaction, button):
        await interaction.response.send_modal(AuthorModal(self.name))

    @discord.ui.button(label="Edit Images", style=discord.ButtonStyle.secondary)
    async def edit_images(self, interaction, button):
        await interaction.response.send_modal(ImageModal(self.name))

    @discord.ui.button(label="Edit Color", style=discord.ButtonStyle.secondary)
    async def edit_color(self, interaction, button):
        await interaction.response.send_modal(ColorModal(self.name))

@tree.command(name="createembed", description="Create a new editable embed", guild=GUILD_ID)
@app_commands.describe(name="Name of your embed")
async def create_embed(interaction: discord.Interaction, name: str):
    if name in embed_profiles:
        await interaction.response.send_message("An embed with this name already exists.", ephemeral=True)
    else:
        embed_profiles[name] = discord.Embed(title="New Embed", description="Customize me!", color=discord.Color.blue())
        save_embed_profiles()
        await interaction.response.send_message(embed=embed_profiles[name], view=EmbedEditorView(name))

class EditEmbedModal(discord.ui.Modal, title="Edit Embed"):
    def __init__(self, name: str, current_title: str, current_description: str):
        super().__init__()
        self.name = name

        self.title_input = discord.ui.TextInput(
            label="Embed Title",
            default=current_title,  # Pre-fill title
            required=False
        )
        self.description_input = discord.ui.TextInput(
            label="Embed Description",
            style=discord.TextStyle.paragraph,
            default=current_description,  # Pre-fill description
            required=False
        )
        self.add_item(self.title_input)
        self.add_item(self.description_input)

    async def on_submit(self, interaction: discord.Interaction):
        settings["greet"][self.name]["embed"]["title"] = self.title_input.value
        settings["greet"][self.name]["embed"]["description"] = self.description_input.value
        save_settings(settings)
        await interaction.response.send_message(f"✅ Embed `{self.name}` updated successfully.", ephemeral=True)


@tree.command(name="editembed", description="Edit the embed content for a greet", guild=GUILD_ID)
@app_commands.describe(name="The name of the greet to edit")
async def editembed(interaction: discord.Interaction, name: str):
    greet = settings.get("greet", {}).get(name)
    if not greet:
        await interaction.response.send_message(f"⚠️ No greet found with the name `{name}`.", ephemeral=True)
        return

    current_title = greet["embed"].get("title", "")
    current_description = greet["embed"].get("description", "")
    await interaction.response.send_modal(EditEmbedModal(name, current_title, current_description))


@tree.command(name="embedshow", description="Show an embed in this channel", guild=GUILD_ID)
@app_commands.describe(name="Name of the embed to show")
async def embed_show(interaction: discord.Interaction, name: str):
    if name not in embed_profiles:
        await interaction.response.send_message("No embed found with that name.", ephemeral=True)
    else:
        await interaction.channel.send(embed=embed_profiles[name])
        await interaction.response.send_message("Embed sent to this channel!", ephemeral=True)

@tree.command(name="setgreet", description="Set the greet channel and embed for a specific name", guild=GUILD_ID)
@app_commands.describe(
    name="The name of this greet",
    channel="The channel to send the greet message",
    image_url="(Optional) Image URL for the embed"
)
async def setgreet(interaction: discord.Interaction, name: str, channel: discord.TextChannel, image_url: str = None):
    if "greet" not in settings:
        settings["greet"] = {}
    settings["greet"][name] = {
        "channel_id": channel.id,
        "embed": {
            "image_url": image_url or ""  # Save as empty string if not provided
        }
    }
    save_settings(settings)
    await interaction.response.send_message(
        f"✅ Greet named `{name}` has been set for channel {channel.mention}.", ephemeral=True
    )

@tree.command(name="listembed", description="List all saved greet embeds", guild=GUILD_ID)
async def listembed(interaction: discord.Interaction):
    greet_data = settings.get("greet", {})
    
    if not greet_data:
        await interaction.response.send_message("ℹ️ No greet embeds have been set yet.", ephemeral=True)
        return

    embed_list = "\n".join(f"• `{name}` → <#{data['channel_id']}>" for name, data in greet_data.items())
    embed = discord.Embed(
        title="📋 Saved Greet Embeds",
        description=embed_list,
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)






class GreetDeleteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        greet_names = list(settings.get("greet", {}).keys())
        if greet_names:
            self.add_item(GreetDeleteSelect(greet_names))

class GreetDeleteSelect(discord.ui.Select):
    def __init__(self, greet_names):
        options = [discord.SelectOption(label=name, value=name) for name in greet_names]
        super().__init__(placeholder="Select a greet to delete", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_name = self.values[0]

        if selected_name in settings.get("greet", {}):
            del settings["greet"][selected_name]
            save_settings(settings)
            await interaction.response.send_message(
                f"🗑️ Greet `{selected_name}` has been deleted.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "⚠️ Greet not found or already deleted.",
                ephemeral=True
            )

async def greet_name_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    greet_data = settings.get("greet", {})
    return [
        app_commands.Choice(name=name, value=name)
        for name in greet_data
        if current.lower() in name.lower()
    ]

@tree.command(name="deleteembed", description="Delete a saved greet embed", guild=GUILD_ID)
@app_commands.describe(name="The name of the greet to delete")
async def deleteembed(interaction: discord.Interaction, name: str):
    if name not in settings.get("greet", {}):
        await interaction.response.send_message(f"⚠️ No greet found with the name `{name}`.", ephemeral=True)
        return

    del settings["greet"][name]
    save_settings(settings)
    await interaction.response.send_message(f"🗑️ Greet `{name}` has been deleted.", ephemeral=True)





@tree.command(name="testgreet", description="Test the greet message using saved settings", guild=GUILD_ID)
@app_commands.describe(name="The name of the greet to test")
async def testgreet(interaction: discord.Interaction, name: str):
    greet = settings.get("greet", {}).get(name)
    if not greet:
        await interaction.response.send_message(f"⚠️ No greet found with the name `{name}`.", ephemeral=True)
        return
    channel = bot.get_channel(greet["channel_id"])
    if not channel:
        await interaction.response.send_message(f"❌ Could not find the saved channel for `{name}`.", ephemeral=True)
        return
    embed_data = greet["embed"]
    replace_map = {
        "{}": interaction.user.mention,
        "{mention}": interaction.user.mention,
        "{username}": interaction.user.name,
        "{member_count}": str(interaction.guild.member_count)
    }
    title = embed_data.get("title", "")
    description = embed_data.get("description", "")
    for key, val in replace_map.items():
        title = title.replace(key, val)
        description = description.replace(key, val)
    embed = discord.Embed(title=title, description=description)
    embed.set_footer(text=f"Tested greet: {name}")
    await channel.send(embed=embed)
    await interaction.response.send_message(f"✅ Greet `{name}` sent to {channel.mention}.", ephemeral=True)
 

class EditEmbedModal(discord.ui.Modal, title="Edit Embed"):
    def __init__(self, name: str):
        super().__init__()
        self.name = name
        greet = settings.get("greet", {}).get(name, {})
        embed = greet.get("embed", {})

        self.title_input = discord.ui.TextInput(
            label="Embed Title",
            default=embed.get("title", ""),
            required=False,
            max_length=256
        )
        self.description_input = discord.ui.TextInput(
            label="Embed Description",
            default=embed.get("description", ""),
            required=False,
            style=discord.TextStyle.paragraph,
            max_length=2000
        )
        self.image_input = discord.ui.TextInput(
            label="Image URL (optional)",
            default=embed.get("image_url", ""),
            required=False,
            max_length=500
        )

        self.add_item(self.title_input)
        self.add_item(self.description_input)
        self.add_item(self.image_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Save the edited values
        settings["greet"][self.name]["embed"]["title"] = self.title_input.value
        settings["greet"][self.name]["embed"]["description"] = self.description_input.value
        if self.image_input.value:
            settings["greet"][self.name]["embed"]["image_url"] = self.image_input.value
        else:
            settings["greet"][self.name]["embed"].pop("image_url", None)

        save_settings(settings)
        await interaction.response.send_message(f"✅ Embed for `{self.name}` has been updated.", ephemeral=True)



@tree.command(name="changeembedset", description="Edit the embed settings for a greet name", guild=GUILD_ID)
@app_commands.describe(name="The greet name you want to edit")
async def changeembedset(interaction: discord.Interaction, name: str):
    greet = settings.get("greet", {}).get(name)
    if not greet:
        await interaction.response.send_message(f"⚠️ No greet found with the name `{name}`.", ephemeral=True)
        return

    await interaction.response.send_modal(EditEmbedModal(name))




@bot.event
async def on_member_join(member):
    greet_settings = settings.get("greet", {})
    for name, data in greet_settings.items():
        channel = bot.get_channel(data["channel_id"])
        if channel:
            embed_data = data["embed"]
            replace_map = {
                "{}": member.mention,
                "{mention}": member.mention,
                "{username}": member.name,
                "{member_count}": str(member.guild.member_count)
            }
            title = embed_data.get("title", "")
            description = embed_data.get("description", "")
            for key, val in replace_map.items():
                title = title.replace(key, val)
                description = description.replace(key, val)
            
            embed = discord.Embed(title=title, description=description)

            # ✅ Optional image support
            image_url = embed_data.get("image_url")
            if image_url:
                embed.set_image(url=image_url)

            await channel.send(embed=embed)

            

        
@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    if before.premium_since is None and after.premium_since is not None:
        try:
            new_nick = f"G-VIP {after.name}"
            if after.nick != new_nick:
                await after.edit(nick=new_nick, reason="User boosted the server")
                print(f"⭐ Changed nickname for {after.name} to {new_nick}")
        except discord.Forbidden:
            print(f"⚠️ Missing permission to change nickname for {after.name}")
        except Exception as e:
            print(f"❌ Error changing nickname: {e}")





@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await tree.sync(guild=GUILD_ID)
    print("✅ Synced slash commands")

bot.run(TOKEN)
