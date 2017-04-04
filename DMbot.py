import discord
import asyncio
import pickle
import os
import pandas as pd
import numpy as np

cmd_token = '!'
# dir = '/Users/albertxu/PycharmProjects/myfirstdiscordbot/'
drafted_poke_file = 'pokeList'
orderFile = 'draftOrder'
adminsFile = 'admins'
my_id = '97477826969616384'

client = discord.Client()

admin_ids = {'97477826969616384': ['286028084287635456']}  #Organized {admin: [servers]}
poke_list = {}  #Drafted pokes.  Structure is '{server: {member: list of pokemon}, s2: {}}'
draft_order = {}    #Drafting order, {server: [queue]}
drafting = {}   #{server: boolean}
draftTier = ''

pokedex = {}
pokedex_names = []


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


#Saves a file <filename> with <contents> inside it.
def save_file(filename, contents):
    pickle.dump(contents, open(filename, 'wb'))


# Deletes non-existent servers; adds previously non-existent servers.
# Basically matches the servers I have info for with the users list.
def update_dict(whichList, listfilename):
    u_server_keys = [s.id for s in client.servers]
    u_poke_list = list(whichList.keys())
    for s in u_server_keys[:]:
        if s in u_poke_list[:]:
            u_server_keys.remove(s)
            u_poke_list.remove(s)
    for k in u_server_keys:
        whichList[k] = {}
    for k in u_poke_list:
        del whichList[k]
    save_file(listfilename, whichList)
    return whichList

@client.event
async def on_ready():
    global poke_list
    global draft_order
    global admin_ids
    global drafting
    global pokedex
    global pokedex_names
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

    poke_list = open_file(drafted_poke_file, {})
    poke_list = update_dict(poke_list, drafted_poke_file)
    draft_order = open_file(orderFile, {s.id: [] for s in client.servers})
    admin_ids = open_file(adminsFile, admin_ids)
    drafting = {s.id: False for s in client.servers}
    pokedex = pickle.load(open('pokedex', 'rb'))
    pokedex_names = [poke['species'].lower() for poke in pokedex.values() if poke['num'] > 0]

    print('Ready!')


#Modifies the queue.
# a- appends all of <data> to cmd, in order.
# i- inserts data[0] at position data[1]
# p- puts data[0] at position data[1], replacing whatever was there originally
# r- replaces all occurrences of data[0] with data[1]
async def to_queue(cmd, sID, data, ret):
    global draft_order
    if cmd == 'a':
        #Does not check whether each person is in the member list or not.
        # Probably should do this sometime soon
        for i in data:
            draft_order[sID].append(i)
        await client.send_message(ret, 'Appended all values to the draft queue.')
    elif cmd=='i':
        try:
            draft_order[sID].insert(data[1], data[0])
            await client.send_message(ret, 'Inserted {} into index {}.'.format(data[0],data[1]))
        except:
            await client.send_message(ret, 'Your syntax was incorrect. The correct syntax is:'
                                           '`sudo mod_queue [server] i [value] [position]`')
    elif cmd=='p':
        try:
            draft_order[sID][data[0]] = data[1]
            await client.send_message(ret, 'Put {} at index {}.'.format(data[0], data[1]))
        except:
            await client.send_message(ret, 'Your syntax was incorrect. The correct syntax is:'
                                           '`sudo mod_queue [server] p [value] [position]`')
    elif cmd=='r':
        draft_order[sID] = [data[1] if x==data[0] else x for x in draft_order[sID]]
        await client.send_message(ret, 'Your syntax was incorrect. The correct syntax is:'
                                       '`sudo mod_queue [server] p [value] [position]`')
    save_file(orderFile, draft_order)


# This script iterates through the drafting order list and asks each person for a response, one by one.
async def draft(sID, ret):
    global drafting
    def strip_msg(msg):
        msg = msg.lower()
        msg = msg.strip()
        if msg.startswith(cmd_token):
            msg = msg[1:]
        msg = msg.strip()
        if msg.startswith('draft'):
            msg = msg[5:]
        msg = msg.strip()

        if msg.startswith('mega'):
            msg = msg[4:]
            msg += '-mega'
        msg = msg.strip()

        if msg.startswith('alolan'):
            msg = msg[6:]
            msg += '-alola'
        elif msg.startswith('alola'):
            msg = msg[5:]
            msg += '-alola'
        msg = msg.strip()

        return msg

    def check(message):
        if not drafting[sID]:
            return False
        msg = strip_msg(message.content)
        # Should be left with just the name now, no spaces.
        # return whether this is pokemon name  or not.
        if msg not in pokedex_names:
            return False
        for team in poke_list[sID].values():
            if msg in team:
                return False
        return True

    while True:
        if not drafting[sID]:
            break
        userID = draft_order[sID][0]
        user = client.get_server(sID).get_member(userID)
        await client.send_message(user, 'Please draft a pokemon by typing in its name.')

        resp = await client.wait_for_message(author=user, check=check)
        item = strip_msg(resp.content)

        if userID in poke_list[sID]:
            poke_list[sID][userID].append(item)
        else:
            poke_list[sID][userID] = [item]
        await client.send_message(user, 'You have drafted {}.'.format(item))
        save_file(drafted_poke_file, poke_list)
        del draft_order[sID][0]
        save_file(orderFile, draft_order)
        if len(draft_order[sID])==0:
            break
    await client.send_message(ret, 'Drafting has ended.')
    drafting[sID] = False


# on_message basically parses the messages.
# private
#   sudo: admin
#     modq: modify queue
#     show: display everybody's picks
#   default: member
#     show: display their own picks
# public
#   admin
#     start/stop draft
#   member
#     See draft order
@client.event
async def on_message(message):
    if message.channel.is_private:
        auth = message.author
        authID = auth.id
        ret = message.channel
        if message.content.startswith(cmd_token):
            msg = message.content[1:].lower().split(' ')
        else:
            msg = message.content.lower().split(' ')
        as_root = False

        # Create an access hole for only myself.
        if authID == my_id:
            if message.content.startswith(cmd_token + 'as '):
                authID = message.content.split(' ')[1]
                del msg[:2]

        #If message is from an admin:
        # -Allow sudo commands
        # -Allow them to add people to the queue
        # -Display everyone's picks
        if authID in admin_ids and msg[0] == 'sudo':
            global drafting
            as_root = True
            del msg[0]

            # Modify the queue.
            if msg[0]=='mod_queue' or msg[0]=='mod_q' or msg[0]=='modq':
                s = admin_ids[authID]
                if len(s) == 1:
                    sID = s[0]
                    del msg[0]
                else:
                    try:
                        sID = msg[1]
                        del msg[:2]
                    except IndexError:
                        await client.send_message(ret, 'Please specify which server.')
                        return
                await to_queue(msg[0], sID, msg[1:], ret)

            # Displays all info for all servers you are admin of.
            elif msg[0] == 'ls' or msg[0] == 'show':
                s = admin_ids[authID]
                for sID in s:
                    server = client.get_server(sID)
                    await client.send_message(auth, '-'*50+'\nMember info for server '+server.name)
                    to_send = ''
                    i = 0
                    for k in poke_list[sID].keys():
                        usr = server.get_member(k)
                        to_send += usr.name + ' id:\t' + k + '\nPokemon: ' + ', '.join(poke_list[sID][k]) + '\n'
                        i += 1
                        if i > 10:
                            await client.send_message(auth, to_send)
                            i = 0
                            to_send = ''
                    if not to_send == '':
                        await client.send_message(auth, to_send)
            # elif as_root and msg[0]=='tier':
            #     global draftTier
            #     draftTier = msg[1]
            #     await client.send_message(auth, 'Drafting tier has been changed to '+msg[1]+'.')
            # elif as_root and msg[0]=='skip':
            #     del draft_order[0]
            #     save_file(orderFile, draft_order)
            #     if len(draft_order) > 0:
            #         await client.send_message(users[draft_order[0]], 'Please draft a pokemon using !draft.')
            #     else:
            #         await client.send_message(client.get_server(server_id).get_channel(channel_id),
            #                                   'Drafting has ended.')
            #         drafting = False

            #Forcefully adds a value to a user.
            # Do later
            elif msg[0] == 'a' or msg[0] == 'add':
                pass #do later

        #Everyone else's possible commands are here.
        # -Show the pokemon you have picked
        if msg[0] == 'ls' or msg[0]=='show':
            if as_root:
                return
            s = [sID for sID in poke_list.keys() if authID in poke_list[sID]]
            for sID in s:
                await client.send_message(auth, '-'*50 +
                                                '\nserver: ' + client.get_server(sID).name +
                                                '\nPokemon: ' + ', '.join(poke_list[sID][authID]))

    #Public message
    elif message.content.startswith(cmd_token):
        auth = message.author
        authID = auth.id
        sID = message.server.id
        ret = message.channel
        msg = message.content[1:].split(' ')

        #If the message is from an admin
        #   start/stop draft
        if authID in admin_ids and sID in admin_ids[authID]:
            if (msg[0]=='begin' or msg[0]=='start') and msg[1]=='draft':
                if drafting[sID]:
                    await client.send_message(ret, 'Drafting has already begun.')
                else:
                    drafting[sID] = True
                    await client.send_message(ret, 'Drafting has begun.')
                    await draft(sID, ret)
                    #Set up a drafting script
            elif (msg[0]=='stop' or msg[0]=='end') and msg[1]=='draft':
                if not drafting[sID]:
                    await client.send_message(ret, 'Drafting has not begun yet.')
                else:
                    drafting[sID] = False
                    await client.send_message(ret, 'Drafting has stopped.')

        #Anyone else
        #   Show the queue
        if msg[0]=='q' or msg[0]=='queue':
            to_show = 15
            to_send = ''
            sID = message.server.id
            if len(draft_order[sID]) == 0:
                await client.send_message(message.channel, 'The queue is empty.')
                return
            que = draft_order[sID][:to_show]
            for i, j in zip(que, range(len(que))):
                member = client.get_server(sID).get_member(i)
                to_send += '{}\t{}\n'.format(j, member.name)
            await client.send_message(message.channel, to_send)

client.run('Mjg2MDI5NTA2NDY3MjAxMDI0.C5c8OA.JznjFmsnDVfV2rVRvvd89ntQAF4')