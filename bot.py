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
        json_data = await ws.recv()
        data = json.loads(json_data)
        print(data)

        if data.get('type') == 'team_join':
            user_id = data.get('user')

            im_channel_id = open_im_channel(user_id)
            if im_channel_id is not None:
                slack.chat.post_message(user_id, "Test message, sent when you message")
                slack.chat.post_message(x['id'], "Hey " + x['name'] + ", welcome to the Devolio Slack group!")
                slack.chat.post_message(x['id'], "We'd love to hear a little about you - feel free to drop" 
                                        + "in on #intro and let everyone know what you're about.")
                slack.chat.post_message(x['id'], "You can add your interests to your profile by clicking on your name, "
                                        + "and then you can join different channels for your various interests "
                                        + "by clicking on that \"Channels\" link up near the top left.")


def get_rtm_uri():
    rtm = slack.rtm.start()
    print(rtm)

    try:
        body = rtm.body
    except slacker.Error as e:
        print(e)
        return None
    return body.get('url')

if __name__ == '__main__':
    ws_url = get_rtm_uri()

    if ws_url is not None:
        asyncio.get_event_loop().run_until_complete(
            read_loop(ws_url)
        )

# Send a message to #general channel
# slack.chat.post_message('#general', 'Hello fellow slackers!')

# while True:
    
    # Get users list
    # response = slack.users.list()
    # users = response.body['members']

    # print(users)

    # for x in users:
        # print(x['id'])
        # slack.chat.post_message(x['id'], 'Hey ' + x['name'] + ', welcome to the Devolio Slack group!')
        # slack.chat.post_message(x['id'], 'We\'d love to hear a little about you - feel free to drop in on #intro and let everyone know what you\'re about.')
        # slack.chat.post_message(x['id'], 'You can add your interests to your profile by [fill this out - I don\'t know what the easiest way to describe this is], and then you can join different channels for your various interests by clicking on that "Channels" link up near the top left [image of Channels link].')

    # time.sleep(500)
