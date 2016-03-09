import os
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

channels = json.loads(slack.channels.list())

for channel in channels.get('channels', {}):
    slack.channels.join(channel.get['id'])


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
                send_introduction_message(user_id, user_name)

        # If a user changes their preferences
        if data.get('type') == "user_change":
            # Get their user id and name
            user_id = data.get('user').get('id')
            user_name = data.get('user').get('name')
            # Make sure im channel is open
            im_channel_id = open_im_channel(user_id)
            # Get info about user
            title = data.get('user').get('profile').get('title')
            print(title)
            if im_channel_id is not None:
                slack.chat.post_message(user_id, "I see you changed your preferences, that's great!")
                slack.chat.post_message(user_id, "I will now put you in some channels that I think might be relevant to you.")
                slack.chat.post_message(user_id, "Feel free to join other channels as well!")
                scan_relevant_channels(user_id)

def get_rtm_uri():
    rtm = slack.rtm.start()
    print(rtm)

    try:
        body = rtm.body
    except slacker.Error as e:
        print(e)
        return None
    return body.get('url')

def scan_relevant_channels(user_id):
    print("Hi")
def send_introduction_message(user_id, user_name):
    slack.chat.post_message(user_id, "Hey " + user_name + ", welcome to the Devolio Slack group!")
    time.sleep(1)
    slack.chat.post_message(user_id, "We'd love to hear a little about you - feel free to drop" \
                                            "in on <#intro> and let everyone know what you're about.")
    time.sleep(1)
    slack.chat.post_message(user_id, "You can add your interests to your profile by clicking on your name, " \
                                            "and then join channels for your various interests " \
                                            "by clicking on that \"Channels\" link up near the top left.")

# Check if this is the main application running (not imported)
if __name__ == '__main__':
    ws_url = get_rtm_uri()

    if ws_url is not None:
        asyncio.get_event_loop().run_until_complete(
            read_loop(ws_url)
        )
