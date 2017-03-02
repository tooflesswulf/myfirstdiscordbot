import discord
import asyncio
import pickle
import os
import pandas as pd
import numpy as np

cmd_token = '!'
# dir = '/Users/albertxu/PycharmProjects/myfirstdiscordbot/'
draftFile = 'draftList'
usersFile = 'userList'
orderFile = 'draftOrder'
my_id = '97477826969616384'
channel_id = '286028084287635456'
df = pd.read_csv('smogon.csv')
pokemonNames = df['Name'][~df['Mega']].as_matrix()

client = discord.Client()
draftList = {}
users = {}
draftID = ['1', '2', '3', '4', '5']
drafting = False
tempList = {}


# Returns the contents of a file <fileName>.  If it does not exist, creates a new file with <default>.
def open_file(filename, default):
    if os.path.exists(os.getcwd()+'/'+filename):
        file = pickle.load(open(filename, 'rb'))
        print(filename + ' loaded.')
        return file
    print(filename + ' does not exist.')
    print('Creating new file ' + filename + '.')
    pickle.dump(default, open(filename, 'wb'))
    return default


def save_file(filename, contents):
    pickle.dump(contents, open(filename, 'wb'))


@client.event
async def on_ready():
    global draftList
    global users
    global draftID
    global tempList
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    users = open_file(usersFile, users)
    for usr in users.keys():
        tempList[usr] = []
    # print(tempList)
    draftList = open_file(draftFile, draftList)
    # print(draftList)
    draftID = open_file(orderFile, draftID)
    print('------')


#<key> is the user ID;  <val> is the value of interest
async def mod_dict(operation, key, val, user, channel=None, flags=None):
    # INSERT INTO <key> <val>
    if operation == 'a':
        if key in draftList.keys():
            if any(val in sublist for sublist in draftList.values()):
                return val + ' already exists elsewhere.', False
            elif val.title() not in pokemonNames:
                return val + ' is not a Pokemon name.', False
            if flags is None:
                draftList[key].append(val)
                save_file(draftFile, draftList)
                return 'Successfully added ' + val + ' to ' + user.name + '.', True
            elif flags == 'temp':
                tempList[key].append(val)
                return 'Successfully added ' + val + ' to ' + user.name + '\'s temporary list.', True
        else:
            return user.name+' does not exist yet.  Type !join to join.', False
    # ADD <key>
    elif operation == 'n':
        if key in draftList.keys():
            return 'You have already joined.', False
        draftList[key] = []
        tempList[key] = []
        users[key] = user
        save_file(usersFile, users)
        save_file(draftFile, draftList)
        return 'Added new member '+user.name, True
    # REMOVE <val> FROM <key>
    elif operation == 'd':
        if flags is None:
            l = draftList
        else:
            l = tempList
        if key in l:
            if val in l[key]:
                l[key].remove(val)
                if flags is None:
                    save_file(draftFile, l)
                    return 'Successfully removed ' + val + ' from ' + user.name + '.', True
                return 'Successfully removed '+val+' from '+user.name+'\'s temporary list.', True
            else:
                return val + ' does not exist under '+user.name+'.', False
        else:
            return key+' does not exist.', False
    # REMOVE * FROM <key>
    elif operation == 'f':
        if key in draftList:
            draftList[key] = []
            save_file(draftFile, draftList)
            return 'Deleted all entries from '+user.name+'.', True
        else:
            return user.name+' does not exist.', False
    # Kill a user
    elif operation == 'k':
        if key in draftList:
            del draftList[key]
            del tempList[key]
            del users[key]
            save_file(usersFile, users)
            save_file(draftFile, draftList)
            return 'Deleted '+key+' from the draft.', True
        else:
            return key+' does not exist.', False


def to_queue(msg):
    if not drafting:
        cmd = msg[1]
        if cmd == 'd':
            pos = []
            for i in range(2, len(msg)):
                n = int(msg[i])
                if n not in pos and n >= -len(draftID) and n < len(draftID):
                    pos.append(n)
            for i in sorted(pos)[::-1]:
                del draftID[i]
        elif cmd == 'a':
            for i in range(2, len(msg)):
                if msg[i] in users:
                    draftID.append(msg[i])
        else:
            usrid = msg[2]
            pos = int(msg[3])
            if usrid in users and 0 <= pos < len(draftID):
                if cmd == 'r':
                    draftID[pos] = usrid
                elif cmd == 'i':
                    draftID.insert(pos, usrid)
        save_file(orderFile, draftID)

@client.event
async def on_message(message):
    if message.channel.is_private:
        auth = message.author
        authID = auth.id
        if message.content.startswith(cmd_token):
            msg = message.content[1:].lower().split(' ')
        else:
            msg = message.content.lower().split(' ')

        # Create an access hole for only myself.
        if authID == my_id:
            if message.content.startswith(cmd_token + 'as '):
                authID = message.content.split(' ')[1]
                del msg[:2]
            elif message.content.startswith(cmd_token + 'k '):
                resp, success = mod_dict('k', msg[1], 0, 0)
                await client.send_message(auth, resp)
            elif msg[0]=='begin_draft':
                global drafting
                if not drafting:
                    drafting = True
                    await client.send_message(users[draftID[0]], 'Please draft a pokemon using !draft.')
                    await client.send_message(client.get_server(channel_id), 'Drafting has begun.')
            elif msg[0]=='toq':
                to_queue(msg)

        if msg[0] == 'ls':
            if authID == my_id:
                await client.send_message(auth, draftList)
                await client.send_message(auth, [(k,v.name) for k, v in users.items()])
            else:
                await client.send_message(auth, 'The pokemon you have currently drafted are:')
                await client.send_message(auth, draftList[authID])
                await client.send_message(auth, 'The pokemon you have in your temporary list are:')
                await client.send_message(auth, tempList[authID])
        elif msg[0]=='a' or msg[0]=='add':
            for i in range(len(msg)-1):
                resp, success = mod_dict('a', authID, msg[i+1], auth, flags='temp')
                await client.send_message(auth, resp)
        elif msg[0]=='draft':
            if authID in users.keys():
                if authID == draftID[0]:
                    resp, success = mod_dict('a', authID, msg[1], users[authID])
                    await client.send_message(auth, resp)
                    if success:
                        await client.send_message(client.get_server(channel_id),
                                                  users[authID].name+' has drafted '+msg[1]+'.')
                        del draftID[0]
                        if len(draftID) > 0:
                            await client.send_message(users[draftID[0]], 'Please draft a pokemon using !draft.')
                        else:
                            await client.send_message(client.get_server(channel_id),
                                                      'Drafting has ended.')

                else:
                    await client.send_message(auth, 'It is not your turn to draft yet.')
        elif msg[0]=='join':
            resp, success = mod_dict('n', authID, 0, auth)
            await client.send_message(auth, resp)
        elif msg[0]=='rm' or msg[0]=='d':
            if msg[1]=='*':
                resp, success = mod_dict('f', authID, 0, auth)
                await client.send_message(auth, resp)
            else:
                for i in range(len(msg)-1):
                    resp, success = mod_dict('d', authID, msg[i+1], auth, flags='temp')
                    await client.send_message(auth, resp)
        elif msg[0]=='queue' or msg[0]=='q':
            if authID == my_id:
                to_send = ''
                for i, j in zip(draftID, range(len(draftID))):
                    to_send += '{}\tuser id: {}\tuser name: {}\n'.format(j, i, users[i].name)
                await client.send_message(auth, to_send)
            else:
                await client.send_message(auth, [users[i].name for i in draftID])

    elif message.content.startswith(cmd_token):
        msg = message.content[1:].split(' ')
        if msg[0]=='join':
            resp = mod_dict('n', message.author.id, 0, user=message.author)
            await client.send_message(message.author, resp)

client.run('Mjg2MDI5NTA2NDY3MjAxMDI0.C5c8OA.JznjFmsnDVfV2rVRvvd89ntQAF4')