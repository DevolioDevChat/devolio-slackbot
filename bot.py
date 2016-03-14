import os
import time
import re
import json

import asyncio
import websockets

import slacker

from shortcuts import shortcuts


################################
# IMPORTANT: just for testing! #
################################
slack = slacker.Slacker('xoxb-24649221783-q40uS6HJkH7D6TMhykeyaH7h')
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
            user_id = data.get('user').get('id')
            user_name = data.get('user').get('name')
            # Open im channel with user
            im_channel_id = open_im_channel(user_id)
            # Send intro message
            if im_channel_id is not None:
                sentences = ["Hey " + user_name + ", welcome to the Devolio Slack group!",
                "We'd love to hear a little about you - feel free to drop" \
                "in on <#intro> and let everyone know what you're about.",
                "You can add your interests to your profile by clicking on your name, " \
                "and then join channels for your various interests " \
                "by clicking on that \"Channels\" link up near the top left."]
                chat_message(sentences, user_id, .8)

        # If a user changes their preferences
        if data.get('type') == "user_change":
            # Get their user id and name
            user_id = data.get('user').get('id')
            user_name = data.get('user').get('name')
            # Make sure im channel is open
            im_channel_id = open_im_channel(user_id)
            user_title = data.get('user').get('profile').get('title')

            # Check to make sure the im channel exists, then find and prompt user for channels to join
            if im_channel_id is not None:
                scan_relevant_channels(user_id, user_title, shortcuts)

        if data.get('type') == "message":
            user_message = data.get('text')
            channel_id = data.get('channel')
            if user_message == "hi":
                chat_message(["Beep boop, I'm a Welcome Bot!"], channel_id, 0)

# Takes an array of lines and sends them to location_id, delayed by delay_time
def chat_message(sentences, location_id, delay_time):
    for sentence in sentences:
        slack.chat.post_message(location_id, sentence, '', 'true' )
        time.sleep(delay_time)

def get_rtm_uri():
    rtm = slack.rtm.start()
    print(rtm)

    try:
        body = rtm.body
    except slacker.Error as e:
        print(e)
        return None
    return body.get('url')

def scan_relevant_channels(user_id, user_title, shortcuts):
    channel_names = get_channel_names()

    # Split user title by words
    user_title = re.split(r"[\,\.\;\&\/\|\s]+", user_title.lower())

    channels_to_suggest = []

    # First check for shortcuts in title
    for real_channel_name in shortcuts:
        for shortcut in shortcuts[real_channel_name]:
            if (shortcut in user_title) or (real_channel_name in user_title):
                channels_to_suggest.append(real_channel_name)

    # Then check for existing channel titles
    for channel_name in channel_names:
        if channel_name in user_title:
            channels_to_suggest.append(channel_name)

    # And finally...
    prompt_channel_join(user_id, channels_to_suggest)

def prompt_channel_join(user_id, channel_names_to_suggest):
    channel_ids_text = ""
    channel_ids = []

    # Add channel ids for each suggested channel that the user isn't already in
    for channel_name in channel_names_to_suggest:
        if not is_user_in_group(user_id, channel_name):
            channel_ids.append(get_channel_id(channel_name))

    # Make a string of links to channels
    for channel_id in channel_ids:
        channel_ids_text += "<#" + channel_id + ">, "
        print("\tadded " + channel_id + " to channel_ids")

    # Remove the last ", " from the string
    channel_ids_text = channel_ids_text[:-2]

    # Actually prompt user to join these channels
    chat_message(["Hey, I noticed you've mentioned " + channel_ids_text + " in your profile. Why not join?"], user_id, 0)

# Check if user is in a group (returns a boolean)
def is_user_in_group(user_id, group_name):
    user_groups = slack.channels.list().body['channels']
    user_list = []
    for group in user_groups:
        if group['name'] == group_name:
            user_list = group['members']
            break
    return user_id in user_list

# List all the channel names
def get_channel_names():
    user_groups = slack.channels.list().body['channels']
    channel_names = []
    for group in user_groups:
        channel_names.append(group['name'])
    return channel_names

# Get a channel id by its name
def get_channel_id(channel_name):
    user_groups = slack.channels.list().body['channels']
    for group in user_groups:
        if group['name'] == channel_name:
            return group['id']

# Check if this is the main application running (not imported)
if __name__ == '__main__':
    ws_url = get_rtm_uri()

    if ws_url is not None:
        asyncio.get_event_loop().run_until_complete(
            read_loop(ws_url)
        )
