import os
import time
import json

import asyncio
import websockets

import slacker


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
                chat_message(sentences, user_id, 3)

        # If a user changes their preferences
        if data.get('type') == "user_change":
            # Get their user id and name
            user_id = data.get('user').get('id')
            user_name = data.get('user').get('name')
            # Make sure im channel is open
            im_channel_id = open_im_channel(user_id)
            user_title = data.get('user').get('profile').get('title')

            if im_channel_id is not None:
                sentences = ["I see you changed your preferences, that's great!",
                "I will now put you in some channels that I think might be relevant to you.",
                "Feel free to join other channels as well!"]
                #chat_message(sentences, user_id, 3)
                scan_relevant_channels(user_id, user_title)

        if data.get('type') == "message":
            user_message = data.get('text')
            channel_id = data.get('channel')
            if user_message == "hi":
                chat_message(["Beep boop, I'm a Welcome Bot!"], channel_id, 0)

def chat_message(sentences, location_id, delay_time):
    for sentence in sentences:
        slack.chat.post_message(location_id, sentence)
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

def scan_relevant_channels(user_id, user_title):
    if "python" in user_title.lower() and is_user_in_group(user_id, 'python') == False:
        chat_message(["You should join <#python>, you're not yet in it!"], user_id, 0)
    if "java" in user_title.lower() and is_user_in_group(user_id, 'java') == False:
        chat_message(["You should join <#java>, you're not yet in it!"], user_id, 0) 
    if "javascript" in user_title.lower() and is_user_in_group(user_id, 'javascript') == False:
        chat_message(["You should join <#javascript>, you're not yet in it!"], user_id, 0)
def is_user_in_group(user_id, group_name):
    user_groups = slack.channels.list().body['channels']
    for group in user_groups:
        if group['name'] == group_name:
            user_list = group['members']
    if user_id not in user_list:
        return False
    return True

# Check if this is the main application running (not imported)
if __name__ == '__main__':
    ws_url = get_rtm_uri()

    if ws_url is not None:
        asyncio.get_event_loop().run_until_complete(
            read_loop(ws_url)
        )
