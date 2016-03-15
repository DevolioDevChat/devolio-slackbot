# Import dependencies
import os
import time
import re
import json

import asyncio
import websockets

import slacker

# Import shortcuts dictionary
from shortcuts import shortcuts


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
        # Try to open an im channel
        response = slack.im.open(user)
    except slacker.Error as e:
        # If that fails print the error and continue
        print(e)
        return None

    # https://api.slack.com/methods/im.open
    return response.body.get('channel', {}).get('id')


async def chat_message(sentence, location_id, ws):
    # Prepare message to send
    body = {
        'type': 'message',
        'token': TOKEN,
        'channel': location_id,
        'text': sentence
    }
    # JSON encode it and send it
    await ws.send(json.dumps(body))


async def scan_relevant_channels(user_id, user_title, channel_id, ws, shortcuts):
    # Get the names of all the channels in the Slack group
    channel_names = get_channel_names()

    # Split what the user has entered as their "job title" into separate words
    user_title = user_title.lower()
    user_title = re.split(r"[\,\.\;\&\/\|\s]+", user_title)

    print("Finding relevant channels...")

    channels_to_suggest = []

    # First check for shortcuts in title
    for channel_name in shortcuts:
        for shortcut in shortcuts[channel_name]:
            if shortcut in user_title:
                channels_to_suggest.append(channel_name)

    # Then check for existing channel titles
    for channel_name in channel_names:
        if channel_name in user_title:
            channels_to_suggest.append(channel_name)

    print("Suggesting these channels:")
    print(channels_to_suggest)

    # Make all the channels into Slack links to the channels...
    recommended_channels = []
    for title in channels_to_suggest:
        # ... as long as they're not already in the channel
        if title in channel_names and not is_user_in_group(user_id, title):
            recommended_channels.append('<#' + channel_names[title] + '>')

    # Make a human-readable list of mentioned channels
    mentioned_channels_text = ""
    for mentioned_channel in channels_to_suggest:
        mentioned_channels_text += mentioned_channel + ', '
    # Trim the last ", "
    mentioned_channels_text = mentioned_channels_text[:-2]

    # Same as above for the channel links
    recommended_channels_text = ""
    for recommended_channel in recommended_channels:
        recommended_channels_text += recommended_channel + ', '
    recommended_channels_text = recommended_channels_text[:-2]

    # Send message to user suggesting channels to join
    if len(recommended_channels_text) > 0:
        await chat_message(
            "Hi, I noticed you've changed your profile and mentioned " + mentioned_channels_text + ". Why not join " + recommended_channels_text + "?",
            channel_id, ws
        )

# Check to see if a user is in a channel
def is_user_in_group(user_id, group_name):
    try:
        # Get list of channels
        user_groups = slack.channels.list().body.get('channels', [])
    except slacker.Error as e:
        print(e)
        return True

    user_list = []
    for group in user_groups:
        if group['name'] == group_name:
            user_list = group['members']
    # This returns true if the user_id is in user_list, otherwise false
    return user_id in user_list

# Get all the channel names from Slack
def get_channel_names():
    try:
        user_groups = slack.channels.list().body.get('channels')
    except slacker.Error as e:
        print(e)
        return []
    return {group['name']: group['id'] for group in user_groups}

# Get a channel id by name
def get_channel_id(channel_name):
    user_groups = slack.channels.list().body['channels']
    for group in user_groups:
        if group['name'] == channel_name:
            return group['id']

async def read_loop(uri):
    ws = await websockets.connect(uri)
    while True:
        # Wait for the data from Slack to come in
        json_data = await ws.recv()
        # Decode it from JSON
        data = json.loads(json_data)

        # Print a confirmation, and print the actual data if it's of an unknown kind
        print("Data received successfully of type " + data.get('type', ''))
        if data.get('type', '') == '':
            print(data)

        # If a user joins the devolio team
        if data.get('type') == 'team_join':
            # Get their user id and name
            user_id = data.get('user', {}).get('id')
            user_name = data.get('user', {}).get('name')
            # Open im channel with user
            im_channel_id = open_im_channel(user_id)
            print("User @" + user_name + " has joined, sending welcome message")
            # Send intro message
            if im_channel_id is not None and get_channel_id('intro') is not None:
                sentences = "Hey @" + user_name + ", welcome to the Devolio Slack group!🙌\n" \
                            "We'd love to hear a little about you - feel free to drop " \
                            "in on <#" + get_channel_id('intro') + "> and let everyone know what you're about.\n" \
                            "You can add your interests to your profile by clicking on your name, " \
                            "and then join channels for your various interests " \
                            "by clicking on that \"Channels\" link up near the top left."
                await chat_message(sentences, im_channel_id, ws)

        # If a user changes their preferences
        if data.get('type') == "user_change":
            # Get their user id and name
            user_id = data.get('user', {}).get('id')
            user_name = data.get('user', {}).get('name')
            
            # Make sure im channel is open
            im_channel_id = open_im_channel(user_id)
            user_title = data.get('user', {}).get('profile', {}).get('title')

            # Check to make sure the im channel exists, then find and prompt user for channels to join
            if im_channel_id is not None and user_title is not None:
                await scan_relevant_channels(user_id, user_title, im_channel_id, ws, shortcuts)

        # If a user sends "hi" to Welcome Bot then respond
        if data.get('type') == "message":
            user_message = data.get('text')
            channel_id = data.get('channel')
            if user_message !='':
                await chat_message(user_message + ", lol", channel_id, ws)

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
