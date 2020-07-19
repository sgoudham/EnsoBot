import asyncio
import datetime

import discord
import mariadb
from decouple import config
from discord import Embed, Forbidden
from discord.ext import commands
from discord.ext.commands import when_mentioned_or

import db
import settings
from settings import blank_space, enso_embedmod_colours, enso_guild_ID, enso_newpeople_ID

# Getting the Bot token from Environment Variables
API_TOKEN = config('DISCORD_TOKEN')

PREFIX = "~"


# Method to allow the commands to be used with mentioning the bot
async def get_prefix(bot, message):
    return when_mentioned_or(PREFIX)(bot, message)


# Bot Initiation
client = commands.Bot(  # Create a new bot
    command_prefix=get_prefix,  # Set the prefix
    description='All current available commands within Ensō~Chan',  # Set a description for the bot
    owner_id=154840866496839680)  # Your unique User ID

# Calls the cogs from the settings.py file and loads them
(anime, helps, fun, modmail) = settings.extensions()
complete_list = anime + helps + fun + modmail
if __name__ == '__main__':
    for ext in complete_list:
        client.load_extension(ext)


# Bot ~Ping command in milliseconds
@client.command(name="ping", aliases=["Ping"])
async def _ping(ctx):
    """Sends the latency of the bot (ms)"""
    await ctx.send(f'Pong! `{round(client.latency * 1000)}ms`')


# Bot event making sure that messages sent by the bot do nothing
@client.event
async def on_message(message):
    # Making sure that the bot does not take in its own messages
    if message.author.bot:
        return

    # Processing the message
    await client.process_commands(message)


# Bot Status on Discord
@client.event
async def on_ready():
    # Tells me that the bot is ready and logged in
    print('Bot is ready.')

    # Sets the bots status on discord for everyone to view
    await client.change_presence(
        activity=discord.Game(name="with yo feelings 😍 😳 🙈"))
    # await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Spider Man 3"))


# Bot event for the bot joining a new guild, storing all users in the database
@client.event
async def on_guild_join(guild):
    try:
        # Set up connection to database
        with db.connection() as conn:
            # Iterate through every member within the guild
            for member in guild.members:
                name = f"{member.name}#{member.discriminator}"

                # Define the insert statement that will insert the user's information
                insert_query = """INSERT INTO members (guildID, discordUser, discordID) VALUES (?, ?, ?)"""
                vals = guild.id, name, member.id,
                with conn.cursor as cursor:
                    # Execute the query
                    cursor.execute(insert_query, vals)
                    print(cursor.rowcount, f"Record inserted successfully into Members from {guild.name}")

            # Define the insert statement for inserting the guild into the guilds table
            insert_query = """INSERT INTO guilds (guildID) VALUES (?)"""
            val = guild.id,
            with conn.cursor as cursor:
                # Execute the query
                cursor.execute(insert_query, val)
                print(cursor.rowcount, f"Record inserted successfully into Guilds from {guild.name}")

    except mariadb.Error as ex:
        print("Parameterized Query Failed: {}".format(ex))


# Bot event for the bot leaving a guild, deleted all users stored in the database
@client.event
async def on_guild_remove(guild):
    try:
        # Set up connection to database
        with db.connection() as conn:
            for member in guild.members:
                # Delete the record of the member as the bot leaves the server
                delete_query = """DELETE FROM members WHERE discordID = (?) AND guildID = (?)"""
                vals = member.id, guild.id,
                with conn.cursor as cursor:
                    # Execute the SQL Query
                    cursor.execute(delete_query, vals)
                    print(cursor.rowcount, f"Record deleted successfully from Members from {guild.name}")

            # Delete the guild and prefix information as the bot leaves the server
            delete_query = """DELETE FROM guilds WHERE guildID = (?)"""
            val = guild.id,
            with conn.cursor as cursor:
                # Execute the query
                cursor.execute(delete_query, val)
                print(cursor.rowcount, f"Record deleted successfully from Guilds from {guild.name}")

    except mariadb.Error as ex:
        print("Parameterized Query Failed: {}".format(ex))


# Bot event for new member joining, sending an embed introducing them to the server
@client.event
async def on_member_join(member):
    # Get the guild
    guild = member.guild

    try:
        # Set up connection to database
        with db.connection() as conn:
            name = f"{member.name}#{member.discriminator}"

            # Define the insert statement that will insert the user's information
            insert_query = """INSERT INTO members (guildID, discordUser, discordID) VALUES (?, ?, ?)"""
            vals = member.guild.id, name, member.id,
            cursor = conn.cursor()

            # Execute the SQL Query
            cursor.execute(insert_query, vals)
            conn.commit()
            print(cursor.rowcount, "Record inserted successfully into Members")

    except mariadb.Error as ex:
        print("Parameterized Query Failed: {}".format(ex))

    # Make sure the guild is Enso
    if guild.id != enso_guild_ID:
        return

    # Set the channel id to "newpeople"
    new_people = guild.get_channel(enso_newpeople_ID)

    # Set the enso server icon and the welcoming gif
    server_icon = guild.icon_url
    welcome_gif = "https://cdn.discordapp.com/attachments/669808733337157662/730186321913446521/NewPeople.gif"

    # Set up embed for the #newpeople channel
    embed = Embed(title="\n**Welcome To Ensō!**",
                  colour=enso_embedmod_colours,
                  timestamp=datetime.datetime.utcnow())

    embed.set_thumbnail(url=server_icon)
    embed.set_image(url=welcome_gif)
    embed.add_field(
        name=blank_space,
        value=f"Hello {member.mention}! We hope you enjoy your stay in this server! ",
        inline=False)
    embed.add_field(
        name=blank_space,
        value=f"Be sure to check out our <#669815048658747392> channel to read the rules and <#683490529862090814> channel to get caught up with any changes! ",
        inline=False)
    embed.add_field(
        name=blank_space,
        value=f"Last but not least, feel free to go into <#669775971297132556> to introduce yourself!",
        inline=False)

    # Send embed to #newpeople
    await new_people.send(embed=embed)


# Bot event for new member joining, sending an embed introducing them to the server
@client.event
async def on_member_remove(member):
    # Get the guild
    guild = member.guild

    try:
        # With the database connection
        with db.connection() as conn:

            # Delete the record of the member as they leave the server
            delete_query = """DELETE FROM members WHERE discordID = (?) AND guildID = (?)"""
            vals = member.id, guild.id,
            cursor = conn.cursor()

            # Execute the SQL Query
            cursor.execute(delete_query, vals)
            conn.commit()
            print(cursor.rowcount, "Record deleted successfully from Members")

    except mariadb.Error as ex:
        print("Parameterized Query Failed: {}".format(ex))


# Bot Event for handling all errors within discord.commands
@client.event
async def on_command_error(ctx, args2):
    # if the user did not specify an user
    if isinstance(args2, commands.MissingRequiredArgument):
        await on_command_missing_user(ctx)
    # if the user has spammed a command and invoked a cooldown
    elif isinstance(args2, commands.CommandOnCooldown):
        await on_command_cooldown(ctx, args2)
    # if the user does not the correct permissions to call a command
    elif isinstance(args2, commands.CheckFailure):
        await on_command_permission(ctx)
    # if the user tries to access a command that isn't available
    elif isinstance(args2, commands.CommandNotFound):
        await on_command_not_found(ctx)
    # if the user provides an argument that isn't recognised
    elif isinstance(args2, commands.BadArgument):
        await on_command_bad_argument(ctx)
    # if the bot does not permissions to send the command
    elif isinstance(args2, Forbidden):
        await on_command_forbidden(ctx)


# Async def for handling command bad argument error
async def on_command_forbidden(ctx):
    # Send an error message to the user telling them that the member specified could not be found
    message = await ctx.send(f"**I don't have permissions to execute this command**")

    # Let the user read the message for 5 seconds
    await asyncio.sleep(5)
    # Delete the message
    await message.delete()


# Async def for handling command bad argument error
async def on_command_bad_argument(ctx):
    # Send an error message to the user telling them that the member specified could not be found
    message = await ctx.send(f'**I could not find that member!**')

    # Let the user read the message for 5 seconds
    await asyncio.sleep(5)
    # Delete the message
    await message.delete()


# Async def for handling command not found error
async def on_command_not_found(ctx):
    # Send an error message to the user telling them that the command doesn't exist
    message = await ctx.send(f'**Command Not Found! Please use `{ctx.prefix}help` to see all commands**')

    # Let the user read the message for 5 seconds
    await asyncio.sleep(5)
    # Delete the message
    await message.delete()


# Async def for handling cooldown error/permission errors
async def on_command_cooldown(ctx, error):
    # Send an error message to the user telling them that the command is on cooldown
    message = await ctx.send(f'That command is on cooldown. Try again in **{error.retry_after:,.2f}** seconds.')

    # Let the user read the message for 5 seconds
    await asyncio.sleep(5)
    # Delete the message
    await message.delete()


# Async def for handling permission errors
async def on_command_permission(ctx):
    # Send an error message to the user saying that they don't have permission to use this command
    message = await ctx.send("**Uh oh! You don't have permission to use this command!**")

    # Let the user read the message for 5 seconds
    await asyncio.sleep(5)
    # Delete the message
    await message.delete()


async def on_command_missing_user(ctx):
    # Send an error message to the user saying that an argument is missing
    message = await ctx.send("**Uh oh! Couldn't find anyone to mention! Try again!**")

    # Let the user read the message for 5 seconds
    await asyncio.sleep(5)
    # Delete the message
    await message.delete()


# Run the bot, allowing it to come online
try:
    client.run(API_TOKEN)
except discord.errors.LoginFailure as e:
    print("Login unsuccessful.")

"""    
def write_to_dm_file(time, author, content):
    with open('images/logs/dm-logs.txt', mode='a') as dm_logs_file:
    dm_logs_file.write(f"{time}: {author}: {content}")
    
    # File Writing Variables
    time = message.created_at
    msg_time = time.strftime('%Y-%m-%dT%H:%M:%S')
    msg_author = message.author
    msg_content = message.content
    

 # Don't count messages that are taken in the dms
    if not isinstance(message.channel, DMChannel):
        # Using connection to the database
        with db.connection() as conn:

            # Make sure that mariaDB errors are handled properly
            try:
                msg_name = message.author.name
                msg_discrim = message.author.discriminator
                time = message.created_at

                # Get:
                guild_id = message.guild.id  # Guild of the message
                msg_time = time.strftime('%Y-%m-%d %H:%M:%S')  # Time of the Message
                msg_author = f"{msg_name}#{msg_discrim}"  # DiscordID
                msg_content = message.content  # Content of the message

                # Store the variables
                val = guild_id, msg_time, msg_author, msg_content,

                # If an attachment (link) has been sent
                if message.attachments:

                    # Loop through all attachments
                    for attachment in message.attachments:
                        # Get the message content and the link that was used
                        attach = "".join(f"Message: {message.content} Link: {attachment.url}")

                    # Define the new variables to send
                    val = guild_id, msg_time, msg_author, attach,

                # Define the Insert Into Statement inserting into the database
                insert_query = """"""INSERT INTO messages (guildID, messageTime, discordID, messageContent) VALUES (?, ?, ?, ?)""""""
                cursor = conn.cursor()

                # Execute the SQL Query
                cursor.execute(insert_query, val)
                conn.commit()
                print(cursor.rowcount, "Record inserted successfully into Logs")

            except mariadb.Error as ex:
                print("Parameterized Query Failed: {}".format(ex))
"""
