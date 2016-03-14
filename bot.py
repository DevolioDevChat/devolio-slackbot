import os
import time
import re
import json

import asyncio
import websockets

import slacker


################################
# IMPORTANT: just for testing! #
################################
TOKEN = 'xoxb-24649221783-q40uS6HJkH7D6TMhykeyaH7h'
slack = slacker.Slacker(TOKEN)
# Use this for production:
#
#     slack = slacker.Slacker(os.environ["SLACKAPIKEY"])
#


def open_im_channel(user):
    try:
        response = slack.im.open(user)
    except slacker.Error as e:
        print(e)
        return None

    # https://api.slack.com/methods/im.open
    return response.body.get('channel', {}).get('id')


async def chat_message(sentences, location_id, delay_time, ws):
    body = {
        'type': 'message',
        'token': TOKEN,
        'channel': location_id
    }
    for sentence in sentences:
        body['text'] = sentence
        await ws.send(json.dumps(body))
        time.sleep(delay_time)


async def scan_relevant_channels(user_id, user_title, ws):
    shortcuts = {
        'web': 'webdev',
        'ror': 'ruby',
        'c++': 'cplusplus',
        'css': 'frontend'
    }
    channel_names = get_channel_names()

    user_title = user_title.lower()
    user_title = re.split(r"[.;&/|\s]", user_title)
    print(user_title)

    for channel_name in channel_names:
        if channel_name in user_title and not is_user_in_group(user_id, channel_name):
            await chat_message(["Hi, I noticed you've put " + channel_name + " in your profile. Why not join #" + channel_name + "?"], user_id, 0, ws)
    for title in user_title:
        if title in shortcuts and not is_user_in_group(user_id, shortcuts[title]):
            await chat_message(["Hi, I noticed you've put " + shortcuts[title] + " in your profile. Why not join #" + shortcuts[title] + "?"], user_id, 0, ws)


def is_user_in_group(user_id, group_name):
    try:
        user_groups = slack.channels.list().body.get('channels', [])
    except slacker.Error as e:
        print(e)
        return True

    user_list = []
    for group in user_groups:
        if group['name'] == group_name:
            user_list = group['members']
    return user_id in user_list


def get_channel_names():
    try:
        user_groups = slack.channels.list().body.get('channels')
    except slacker.Error as e:
        print(e)
        return []

    return [group['name'] for group in user_groups]


async def read_loop(uri):
    ws = await websockets.connect(uri)
    while True:
        # Wait for the data from slack to come in
        json_data = await ws.recv()
        data = json.loads(json_data)
        print(data)

        # If a user joins the devolio team
        if data.get('type') == 'team_join':
            # Get their user id and name
            user_id = data.get('user', {}).get('id')
            user_name = data.get('user', {}).get('name')
            # Open im channel with user
            im_channel_id = open_im_channel(user_id)
            # Send intro message
            if im_channel_id is not None:
                sentences = ["Hey " + user_name + ", welcome to the Devolio Slack group!",
                             "We'd love to hear a little about you - feel free to drop"
                             "in on <#intro> and let everyone know what you're about.",
                             "You can add your interests to your profile by clicking on your name, "
                             "and then join channels for your various interests "
                             "by clicking on that \"Channels\" link up near the top left."]
                await chat_message(sentences, im_channel_id, .8, ws)

        # If a user changes their preferences
        if data.get('type') == "user_change":
            # Get their user id
            user_id = data.get('user', {}).get('id')
            # Make sure im channel is open
            im_channel_id = open_im_channel(user_id)
            user_title = data.get('user', {}).get('profile', {}).get('title')

            if im_channel_id is not None:
                await scan_relevant_channels(user_id, user_title, ws)

        if data.get('type') == "message":
            user_message = data.get('text')
            channel_id = data.get('channel')
            if user_message == "hi":
                await chat_message(["Beep boop, I'm a Welcome Bot!"], channel_id, 0, ws)


def get_rtm_uri():
    rtm = slack.rtm.start()

    try:
        body = rtm.body
    except slacker.Error as e:
        print(e)
        return None
    return body.get('url')

# Check if this is the main application running (not imported)
if __name__ == '__main__':
    ws_url = get_rtm_uri()

    if ws_url is not None:
        asyncio.get_event_loop().run_until_complete(
            read_loop(ws_url)
        )
