import discord
import asyncio
import pickle
import os
import numpy as np

TEMP_PIPE = '330105317855854593'

cmd_token = '!'
show_picks = False
# dir = '/Users/albertxu/PycharmProjects/myfirstdiscordbot/'
drafted_poke_file = 'pokeList.pkl'
orderFile = 'draftOrder.pkl'
adminsFile = 'admins.pkl'
my_id = '97477826969616384'
tiers = ['uber', 'ou', 'bl', 'uu', 'bl2','ru','bl3','nu','pu','lc']

profanities = ['fuck','cunt','pussy','bitch','fcuk','fukc','nigger','nigga','jiggaboo','shitlicker','fag','cock']

client = discord.Client()

admin_ids = {'97477826969616384': ['286028084287635456','297735108293558274','280108153490898945']}  #Organized {admin: [servers]}
poke_list = {}  #Drafted pokes.  Structure is '{server: {member: list of pokemon}, s2: {}}'
draft_order = {}    #Drafting order, {server: [queue]}
drafting = {}   #{server: boolean}
draftingcounter = {} #{server: int} Counts the number of starts/stops
undos = {} #{server: [(last_user, last_poke), (2nd_last, 2nd_last)]}
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


def key_gen(whichList):
    skeys = [s.id for s in client.servers]
    lkeys = list(whichList.keys())
    for sk in skeys:
        if sk not in lkeys:
            yield sk


# Deletes non-existent servers; adds previously non-existent servers.
# Basically matches the servers I have info for with the users list.
def update_dict(whichList, listfilename, default):
    new_key_gen = key_gen(whichList)
    for k in new_key_gen:
        whichList[k] = default.copy()
    for k in whichList.keys():
        if k not in [s.id for s in client.servers]:
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
    poke_list = update_dict(poke_list, drafted_poke_file, {})
    draft_order = open_file(orderFile, {s.id: [] for s in client.servers})
    draft_order = update_dict(draft_order, orderFile, [])
    admin_ids = open_file(adminsFile, admin_ids)
    drafting = {s.id: False for s in client.servers}
    pokedex = pickle.load(open('dex_min.pkl', 'rb'))
    pokedex_names = [poke for poke in pokedex.keys()]

    print('Ready!')


#Modifies the queue.
# a- appends all of <data> to cmd, in order.
# i- inserts data[0] at position data[1]
# p- puts data[0] at position data[1], replacing whatever was there originally
# r- replaces all occurrences of data[0] with data[1]
async def to_queue(cmd, sID, data, ret):
    global draft_order
    if cmd == 'a':
        for i in data:
            if client.get_server(sID).get_member(i)is None:
                await client.send_message(ret, 'Member with id {} does not exist in this server. Aborting.'.format(i))
                return
        for i in data:
            draft_order[sID].append(i)
        await client.send_message(ret, 'Appended all values to the draft queue.')
    elif cmd=='i':
        try:
            usr, pos = data[0], int(data[1])
            usrname = client.get_server(sID).get_member(usr)
            if client.get_server(sID).get_member(usr) is None:
                await client.send_message(ret, 'Member with id {} does not exist in this server. Aborting.'.format(usr))
                return
            draft_order[sID].insert(pos, usr)
            await client.send_message(ret, 'Inserted {}({}) into index {}.'.format(
                                      usrname, usr,pos))
        except:
            await client.send_message(ret, 'Your syntax was incorrect. The correct syntax is:'
                                           '`sudo mod_queue [server] i [value] [position]`')
    elif cmd=='p':
        try:
            usr, pos = data[0], int(data[1])
            usrname = client.get_server(sID).get_member(usr)
            if client.get_server(sID).get_member(usr) is None:
                await client.send_message(ret, 'Member with id {} does not exist in this server. Aborting.'.format(usr))
                return
            draft_order[sID][pos] = usr
            await client.send_message(ret, 'Put {}({}) at index {}.'.format(usrname, usr, pos))
        except:
            await client.send_message(ret, 'Your syntax was incorrect. The correct syntax is:'
                                           '`sudo mod_queue [server] p [value] [position]`')
    elif cmd=='r':
        try:
            to_rep, rep = data[0], data[1]
            usrname = client.get_server(sID).get_member(rep)
            if rep in ['none','None','0','.','-']:
                draft_order[sID] = [x for x in draft_order[sID] if x!=rep]
            if client.get_server(sID).get_member(rep) is None:
                await client.send_message(ret, 'Member with id {} does not exist in this server. Aborting.'.format(rep))
                return
            draft_order[sID] = [rep if x==to_rep else x for x in draft_order[sID]]
            await client.send_message(ret, 'Replaced all instances of {} with {}({})'.format(
                                      to_rep, usrname, rep))
        except:
            await client.send_message(ret, 'Your syntax was incorrect. The correct syntax is:'
                                           '`sudo mod_queue [server] r [to_replace] [replace_with]`')
    elif cmd=='d':
        try:
            index = int(data[0])
        except:
            await client.send_message(ret, 'Your syntax was incorrect. The correct syntax is:'
                                           '`sudo mod_queue [server] d [index]`')
            return
        try:
            mem = draft_order[sID][index]
            usrname = client.get_server(sID).get_member(mem)
            await client.send_message(ret, 'Deleted {}({}) at index {}.'.format(
                                      usrname, mem, index))
            del draft_order[sID][index]
        except IndexError:
            await client.send_message(ret, 'Index out of bounds.')
    else:
        await client.send_message(ret, 'Your syntax was incorrect. The correct syntax is:'
                                       '`sudo mod_queue [server] [cmd] [*args]`')
    save_file(orderFile, draft_order)


#Removes a pokemon from a user.
async def remove_pokemon(ret, sID, usr, poke_name):
    if poke_name == '*':
        del poke_list[sID][usr]
        await client.send_message(ret, '{}\'s list has been cleared.'.format(usr))
        save_file(drafted_poke_file, poke_list)
        return
    if poke_name not in poke_list[sID][usr]:
        await client.send_message(ret, '{} is not in {}\'s list.'.format(poke_name, usr))
        return
    poke_list[sID][usr].remove(poke_name)
    await client.send_message(ret, '{} has been removed from {}\'s list.'.format(poke_name, usr))
    if len(poke_list[sID][usr]) == 0:
        del poke_list[sID][usr]
    save_file(drafted_poke_file, poke_list)
    return

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
        msg = strip_msg(message.content)
        # Should be left with just the name now, no spaces.
        # return whether this is pokemon name  or not.
        if msg not in pokedex_names:
            return False, message.channel, "I cannot recognize this as a pokemon name."
        for team in poke_list[sID].values():
            if msg in team:
                return False, message.channel, "Someone else has already drafted this."
        return True, message.channel, 0

    counter = draftingcounter[sID]
    while True:
        userID = draft_order[sID][0]
        user = client.get_server(sID).get_member(userID)
        await client.send_message(user, 'Please draft a pokemon by typing in its name.')
        await client.send_message(ret, '{}'.format(user.name) +
                                  '\'s turn to draft.\nPlease draft a pokemon by typing in its name.')

        resp = await client.wait_for_message(author=user)
        if not (show_picks or resp.channel.is_private):
            try:
                await client.delete_message(resp)
                await client.send_message(user, "You just typed '{}' to me.".format(resp.content))
            except:
                pass
        valid, src, err = check(resp)
        while counter==draftingcounter[sID] and not valid:
            await client.send_message(src, err)
            resp = await client.wait_for_message(author=user)
            if counter==draftingcounter[sID]:
                if not (show_picks or resp.channel.is_private):
                    try:
                        await client.delete_message(resp)
                        await client.send_message(user, "You just typed '{}' to me.".format(resp.content))
                    except:
                        pass
            valid, src, err = check(resp)

        if counter != draftingcounter[sID]:
            return

        item = strip_msg(resp.content)

        await add_poke(sID, userID, item, ret)
        if len(draft_order[sID]) == 0:
            break
    await client.send_message(ret, 'Drafting has ended.')
    drafting[sID] = False
    draftingcounter[sID] += 1


# Adds pokemon to a user's list.
# Also removed the first member of the queue.
async def add_poke(sID, userID, item, ret):
    user = client.get_server(sID).get_member(userID)
    if userID in poke_list[sID]:
        poke_list[sID][userID].append(item)
    else:
        poke_list[sID][userID] = [item]

    if show_picks:
        await client.send_message(ret, '{} has drafted {}.\nTier: {}'.format(user.name, item, pokedex[item]))
        await client.send_message(ret, 'http://www.smogon.com/dex/media/sprites/xy/{}.gif'.format(item))

    # DELETE THIS LATER
    else:
        send_to = client.get_server(sID).get_channel(TEMP_PIPE)
        if send_to:
            await client.send_message(send_to, '{} has drafted {}.\nTier: {}'.format(user.name, item, pokedex[item]))
            await client.send_message(send_to, 'http://www.smogon.com/dex/media/sprites/xy/{}.gif'.format(item))
    # DELETE THIS LATER

    save_file(drafted_poke_file, poke_list)
    del draft_order[sID][0]
    save_file(orderFile, draft_order)
    if sID in undos.keys():
        undos[sID].insert(0, (userID, item))
    else:
        undos[sID] = [(userID, item)]

# on_message basically parses the messages.
# private
#   sudo: admin
#     modq: modify queue
#     show: display everybody's picks
#   default: member
#     show: display their own picks
# public (!)
#   admin
#     start draft: starts the draft system
#     end draft: stops the draft
#   member
#     See draft order
@client.event
async def on_message(message):
    if not message.channel.is_private and message.server.id == '280108153490898945':
        cont = message.content.lower()
        for w in profanities:
            if w in cont:
                await client.delete_message(message)
                return

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
                        await client.send_message(ret, 'Please specify which server.\n'+
                                                       '`sudo modq [server] ...`')
                        return
                await to_queue(msg[0], sID, msg[1:], ret)

            # Displays all info for all servers you are admin of.
            elif msg[0] == 'ls' or msg[0] == 'show':
                s = admin_ids[authID]
                for sID in s:
                    server = client.get_server(sID)
                    await client.send_message(auth, '-'*50+'\nMember info for server {}, id {}'.format(server.name, sID))
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
            elif msg[0] in ['a', 'add']:
                pass #do later
            elif msg[0] in ['rm','del','d','remove','delete']:
                s = admin_ids[authID]
                if len(s) == 1:
                    sID = s[0]
                    del msg[0]
                else:
                    try:
                        sID = msg[1]
                        del msg[:2]
                    except IndexError:
                        await client.send_message(ret, 'Please specify which server.\n' +
                                                  '`sudo rm [server] [user] [pokemon_name]`')
                        return
                try:
                    usr = msg[0]
                    poke_name = msg[1]
                except IndexError:
                    await client.send_message(ret, 'Incorrect syntax.\n' +
                                              '`sudo rm [server] [user] [pokemon_name]`')
                    return
                await remove_pokemon(ret, sID, usr, poke_name)
                return

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
                    if sID in draftingcounter.keys():
                        draftingcounter[sID] += 1
                    else:
                        draftingcounter[sID] = 0
                    await client.send_message(ret, 'Drafting has begun.')
                    await draft(sID, ret)
            elif msg[0]=='pause' or (msg[0]=='stop' or msg[0]=='end') and msg[1]=='draft':
                if not drafting[sID]:
                    await client.send_message(ret, 'Drafting has not begun yet.')
                else:
                    draftingcounter[sID] += 1
                    drafting[sID] = False
                    await client.send_message(ret, 'Drafting has stopped.')
            elif msg[0]=='undo':
                if not drafting[sID]:
                    await client.send_message(ret, 'Drafting has not begun yet.  Nothing to undo.')
                elif sID not in undos.keys():
                    await client.send_message(ret, 'Cannot undo anything.')
                else:
                    drafting[sID] = False
                    last_user, last_poke = undos[sID][0]
                    del undos[sID][0]
                    if len(undos[sID]) == 0:
                        del undos[sID]
                    await to_queue('i', sID, (last_user, 0), auth)
                    await remove_pokemon(auth,sID,last_user,last_poke)
                    drafting[sID] = True
                    draftingcounter[sID] += 1
                    await client.send_message(ret, 'Undo\'d the last action.')
                    await draft(sID, ret)
            elif msg[0]=='skip':
                try:
                    to_add = message.content[6:]
                    if to_add == '':
                        to_add = 'sunkern'
                except IndexError:
                    to_add = 'sunkern'
                if not drafting[sID]:
                    await client.send_message(ret, 'Drafting has not begun yet.  Nothing to skip.')
                else:
                    drafting[sID] = False
                    userID = draft_order[sID][0]
                    draftingcounter[sID] += 1
                    await add_poke(sID, userID, to_add, ret)
                    await client.delete_message(message)
                    drafting[sID] = True
                    await draft(sID, ret)

        #Anyone else
        #   Show the queue
        if msg[0]=='q' or msg[0]=='queue':
            e = 16
            try:
                e = int(msg[1])
            except:
                pass
            to_send = ''
            if len(draft_order[sID]) == 0:
                await client.send_message(ret, 'The queue is empty.')
                return
            que = draft_order[sID][:e]
            for i, j in zip(que, range(len(que))):
                member = client.get_server(sID).get_member(i)
                to_send += '{}\t{}\n'.format(j, member.name)
            await client.send_message(ret, to_send)
        elif msg[0] in ['picked']:
            tier = []
            for t in msg[1:]:
                try:
                    assert t.lower() in tiers
                    tier.append(t.lower())
                except:
                    pass
            full_list = []
            for pokes in poke_list[sID].values():
                for p in pokes:
                    try:
                        if tier == [] or pokedex[p][0].lower() in tier:
                            full_list.append(p)
                    except:
                        pass
            to_send = ', '.join(sorted(full_list))
            if to_send != '':
                await client.send_message(ret, to_send)
            else:
                await client.send_message(ret, 'NO PICKS YET.')

client.run('Mjg2MDI5NTA2NDY3MjAxMDI0.C5c8OA.JznjFmsnDVfV2rVRvvd89ntQAF4')