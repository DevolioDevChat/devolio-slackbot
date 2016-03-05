from slacker import Slacker
import time

slack = Slacker('xoxb-24649221783-q40uS6HJkH7D6TMhykeyaH7h')

rtm = slack.rtm.start()
print(rtm)

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
