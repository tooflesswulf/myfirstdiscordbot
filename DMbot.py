import discord
import asyncio
import pickle
import os

cmd_token = '!'
dir = '/Users/albertxu/PycharmProjects/myfirstdiscordbot/'
saveFile = 'savedList'

client = discord.Client()

draftList = {'97477826969616384': []}


@client.event
async def on_ready():
    global draftList
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
    pickle.dump(draftList, open(saveFile, 'wb'))


def mod_dict(operation, key, val, user=None, channel=None):
    # Add <val> to <key>
    if operation == 'a':
        if key in draftList.keys():
            if any(val in sublist for sublist in draftList.values()):
                return val + ' already exists elsewhere.'
            draftList[key].append(val)
        else:
            return user.name+' does not exist yet.  Go to <general> and type !join.'
        save_draft()
        return 'Successfully added '+val+' to '+user.name+'.'
    # New member
    elif operation == 'n':
        if key in draftList.keys():
            return 'You have already joined.'
        draftList[key] = []
        save_draft()
        return 'Added new member '+user.name
    elif operation == 'd':
        if key in draftList:
            if len(draftList[key])==0:
                del draftList[key]
                return 'Successfully removed '+val+' from '+key+'.'
            if val in draftList[key]:
                draftList[key].remove(val)
                save_draft()
                return 'Successfully removed '+val+' from '+key+'.'
            else:
                return val + 'does not exist under '+key+'.'
        else:
            return key+' does not exist.'
    elif operation == 'f':
        if key in draftList:
            draftList[key] = []
            save_draft()
            return 'Deleted all entries in '+key+'.'
        else:
            return key+' does not exist.'


@client.event
async def on_message(message):
    if message.channel.is_private:
        auth = message.author
        if message.content.startswith(cmd_token):
            msg = message.content[1:].lower().split(' ')
        else:
            msg = message.content.lower().split(' ')
        if msg[0]=='ls':
            if auth.id == '97477826969616384':
                await client.send_message(auth, draftList)
            # await client.send_message(message.channel, 'gottem')
        elif msg[0]=='a' or msg[0]=='add':
            for i in range(len(msg)-1):
                resp = mod_dict('a', auth.id, msg[i+1], user=auth)
                await client.send_message(auth, resp)
        elif msg[0]=='join':
            resp = mod_dict('n', auth.id, 0, user=auth)
            await client.send_message(auth, resp)

    elif message.content.startswith(cmd_token):
        msg = message.content[1:].split(' ')
        print(msg)
        if msg[0]=='join':
            resp = mod_dict('n', message.author.id, 0, user=message.author)
            await client.send_message(message.author, resp)



client.run('Mjg2MDI5NTA2NDY3MjAxMDI0.C5c8OA.JznjFmsnDVfV2rVRvvd89ntQAF4')