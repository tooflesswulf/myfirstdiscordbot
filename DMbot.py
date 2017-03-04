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
admin_ids = ['97477826969616384']
my_id = '97477826969616384'
channel_id = '286028084287635456' # test general
server_id = '286028084287635456' # test
#server_id = '280108153490898945' # WPCL
#channel_id = '280108153490898945' # WPCL general
df = pd.read_csv('smogon.csv')
pokemonNames = df['Name'][~df['Mega']].as_matrix()

client = discord.Client()
draftList = {}
users = {}
draftID = []
drafting = False
tempList = {}
draftTier = ''


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
async def mod_dict(operation, key, val, user, channel=None, flags=None, admin=False):
    # INSERT INTO <key> <val>
    if operation == 'a':
        if key in users.keys():
            if not admin and any(val in sublist for sublist in draftList.values()):
                await client.send_message(user, val + ' already exists elsewhere.')
                return False
            elif not admin and val.title() not in pokemonNames:
                await client.send_message(user, val + ' is not a Pokemon name.')
                return False
            if flags is None:
                draftList[key].append(val)
                save_file(draftFile, draftList)
                await client.send_message(user, 'Successfully added ' + val + ' to ' + users[key].name + '.')
                await client.send_message(client.get_server(channel_id), users[key].name + ' has drafted ' + val + '.')
                return True
            elif flags == 'temp':
                tempList[key].append(val)
                await client.send_message(user, 'Successfully added ' + val + ' to ' + users[key].name + '\'s temporary list.')
                return True
        else:
            await client.send_message(user, key+' does not exist yet.  Type !join to join.')
            return False
    # ADD <key>
    elif operation == 'n':
        if key in draftList.keys():
            await client.send_message(user, 'You have already joined.')
            return False
        draftList[key] = []
        tempList[key] = []
        users[key] = user
        save_file(usersFile, users)
        save_file(draftFile, draftList)
        await client.send_message(user, 'Added new member '+users[key].name)
        return True
    # REMOVE <val> FROM <key>
    elif operation == 'd':
        if flags is None:
            l = draftList
        elif flags=='temp':
            l = tempList
        if key in l:
            if val in l[key]:
                l[key].remove(val)
                if flags is None:
                    save_file(draftFile, l)
                    await client.send_message(user, 'Successfully removed ' + val + ' from '
                                              + users[key].name + '\'s list.')
                    return True
                else:
                    await client.send_message(user, 'Successfully removed ' + val + ' from '
                                              + users[key].name + '\'s temporary list.')
            else:
                await client.send_message(user, val + ' does not exist under '+users[key].name+'.')
                return False
        else:
            await client.send_message(user, key+' does not exist.')
            return False
    # REMOVE * FROM <key>
    elif operation == 'f':
        if key in draftList:
            if flags == 'temp':
                tempList[key] = []
                await client.send_message(user, 'Deleted all entries from '
                                          + users[key].name + '\'s temporary list.')
                return True
            draftList[key] = []
            save_file(draftFile, draftList)
            await client.send_message(user, 'Deleted all entries from '+users[key].name+'.')
            return True
        else:
            await client.send_message(user, key+' does not exist.')
            return False
    # Kill a user
    elif operation == 'k':
        if key in draftList:
            del draftList[key]
            del tempList[key]
            del users[key]
            while key in draftID:
                draftID.remove(key)
            save_file(usersFile, users)
            save_file(draftFile, draftList)
            save_file(orderFile, draftID)
            await client.send_message(user, 'Deleted '+key+' from the draft.')
            return True
        else:
            await client.send_message(user, key+' does not exist.')
            return False


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

        is_admin = False
        targ = '0'
        if authID in admin_ids:
            if msg[0] == 'sudo':
                is_admin = True
                if msg[1] in users:
                    targ = msg[1]
                    del msg[:2]
                else:
                    del msg[0]

        # Create an access hole for only myself.
        if authID == my_id:
            if message.content.startswith(cmd_token + 'as '):
                authID = message.content.split(' ')[1]
                del msg[:2]
            elif message.content.startswith(cmd_token + 'k '):
                await mod_dict('k', msg[1], 0, auth)

        if authID in admin_ids:
            global drafting
            if msg[0]=='begin_draft':
                if not drafting:
                    drafting = True
                    await client.send_message(client.get_server(server_id).get_channel(channel_id), 'Drafting has begun.')
                    await client.send_message(users[draftID[0]], 'Please draft a pokemon using !draft.')
            elif msg[0]=='stop_draft':
                if drafting:
                    drafting = False
                    await client.send_message(client.get_server(server_id).get_channel(channel_id), 'Drafting has ended or paused.')
            elif msg[0]=='toq':
                to_queue(msg)
            elif is_admin and msg[0]=='tier':
                global draftTier
                draftTier = msg[1]
                await client.send_message(auth, 'Drafting tier has been changed to '+msg[1]+'.')

        if msg[0] == 'ls':
            if is_admin:
                to_send = ''
                for k, v in users.items():
                    to_send += v.name+' id:\t'+k+'\nPokemon: '+', '.join(draftList[k])+'\n'
                await client.send_message(auth, to_send)
            else:
                await client.send_message(auth, 'The pokemon you have currently drafted are:\n'+
                                          ', '.join(draftList[authID]))
                await client.send_message(auth, 'The pokemon you have in your temporary list are:\n'+
                                          ', '.join(tempList[authID]))
        elif msg[0]=='a' or msg[0]=='add':
            for i in range(len(msg)-1):
                if is_admin:
                    await mod_dict('a', targ, msg[i+1], auth, admin=True)
                else:
                    await mod_dict('a', authID, msg[i+1], auth, flags='temp')
        elif msg[0]=='draft':
            # global drafting
            if drafting and authID in users.keys():
                if authID == draftID[0]:
                    success = await mod_dict('a', authID, msg[1], users[authID])
                    if success:
                        del draftID[0]
                        save_file(orderFile, draftID)
                        if len(draftID) > 0:
                            await client.send_message(users[draftID[0]], 'Please draft a pokemon using !draft.')
                        else:
                            await client.send_message(client.get_server(server_id).get_channel(channel_id),
                                                      'Drafting has ended.')
                            drafting = False

                else:
                    await client.send_message(auth, 'It is not your turn to draft yet.')
        elif msg[0]=='join':
            await mod_dict('n', authID, 0, auth)
        elif msg[0]=='rm' or msg[0]=='d':
            if msg[1]=='*':
                if is_admin:
                    await mod_dict('f', targ, 0, auth, admin=True)
                else:
                    await mod_dict('f', authID, 0, auth, flags='temp')
            else:
                for i in range(len(msg)-1):
                    if is_admin:
                        await mod_dict('d', targ, msg[i+1], auth)
                    else:
                        await mod_dict('d', authID, msg[i+1], auth, flags='temp')
        elif msg[0]=='queue' or msg[0]=='q':
            if len(draftID) == 0:
                await client.send_message(auth, 'The queue is empty.')
            elif is_admin:
                to_send = ''
                for i, j in zip(draftID[:5], range(len(draftID[:5]))):
                    to_send += '{}\tuser id: {}\tuser name: {}\n'.format(j, i, users[i].name)
                await client.send_message(auth, to_send)
            else:
                to_send = ''
                for i, j in zip(draftID[:5], range(len(draftID[:5]))):
                    to_send += '{}\t{}\n'.format(j, users[i].name)
                await client.send_message(auth, to_send)
    elif message.content.startswith(cmd_token):
        msg = message.content[1:].split(' ')
        if msg[0]=='join':
            await mod_dict('n', message.author.id, 0, user=message.author)

client.run('Mjg2MDI5NTA2NDY3MjAxMDI0.C5c8OA.JznjFmsnDVfV2rVRvvd89ntQAF4')