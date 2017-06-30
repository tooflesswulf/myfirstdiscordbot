import discord
import asyncio

client = discord.Client()

serv = '280108153490898945'
auth = ['270685668403970048', '97477826969616384']

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

    print('Ready!')

@client.event
async def on_message(message):
    s_id = message.server.id
    auth_id = message.author.id
    if auth_id in auth:
        print('hi')
        await client.delete_message(message)


client.run('Mjg2MDI5NTA2NDY3MjAxMDI0.C5c8OA.JznjFmsnDVfV2rVRvvd89ntQAF4')
