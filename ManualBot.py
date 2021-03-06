import discord
import asyncio
import pickle
import os

cmd_token = '!'
dir = '/Users/albertxu/PycharmProjects/myfirstdiscordbot/'
saveFile = 'savedList'

client = discord.Client()

poke_list = {'admin': ['test']}


@client.event
async def on_ready():
    global poke_list
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    # print(os.getcwd())
    if os.path.exists(os.getcwd()+'/'+saveFile):
        print('save file Loaded.')
    else:
        print('save file does not exist at:', os.getcwd()+saveFile)
        print('Creating new saveFile.')
        pickle.dump(draftList, open(saveFile, 'wb'))
    draftList = pickle.load(open(saveFile, 'rb'))
    print('------')


def save_draft():
    pickle.dump(poke_list, open(saveFile, 'wb'))


def mod_dict(operation, key, val):
    if operation == 'a':
        if key in poke_list:
            if any(val in sublist for sublist in poke_list.values()):
                return val + ' already exists elsewhere.'
            poke_list[key].append(val)
        else:
            poke_list[key] = [val]
        save_draft()
        return 'Successfully added '+val+' to '+key+'.'
    elif operation == 'd':
        if key in poke_list:
            if len(poke_list[key])==0:
                del poke_list[key]
                return 'Successfully removed '+val+' from '+key+'.'
            if val in poke_list[key]:
                poke_list[key].remove(val)
                save_draft()
                return 'Successfully removed '+val+' from '+key+'.'
            else:
                return val + 'does not exist under '+key+'.'
        else:
            return key+' is currently empty.'
    elif operation == 'f':
        if key in poke_list:
            del poke_list[key]
            save_draft()
            return 'Deleted all entries in '+key+'.'
        else:
            return key+' is currently empty.'


@client.event
async def on_message(message):
    if message.content.startswith(cmd_token):
        msg = message.content[1:].split()
        print(msg)
        if msg[0] == 'test':
            counter = 0
            tmp = await client.send_message(message.channel, 'Calculating messages...')
            async for log in client.logs_from(message.channel, limit=100):
                if log.author == message.author:
                    counter += 1

            await client.edit_message(tmp, 'You have {} messages.'.format(counter))
        elif msg[0] == 'printq':
            await client.send_message(message.channel, poke_list)
        elif msg[0] == 'add':
            for i in range(len(msg)-1):
                resp = mod_dict('a', message.channel.name, msg[i + 1])
                await client.send_message(message.channel, resp)
        elif msg[0] == 'rm':
            for i in range(len(msg)-1):
                resp = mod_dict('d', message.channel.name, msg[i + 1])
                await client.send_message(message.channel, resp)
        elif msg[0] == 'flush':
            resp = mod_dict('f', message.channel.name, 0)
            await client.send_message(message.channel, resp)


client.run('Mjg2MDI5NTA2NDY3MjAxMDI0.C5c8OA.JznjFmsnDVfV2rVRvvd89ntQAF4')