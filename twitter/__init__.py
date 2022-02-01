
from datetime import datetime, timezone
import json
import logging
import os
import requests

import azure.functions as func

# https://birdie0.github.io/discord-webhooks-guide/discord_webhook.html

def tweets_to_webhooks(tweets:dict):
    users = {}
    
    for user in tweets['includes']['users']:
        users[user['id']] = {
            'name': user['name'],
            'profile_image_url': user['profile_image_url'],
            'username': user['username'],
        }

    for tweet in tweets['data']:

        # Resolve original RT
        if "referenced_tweets" in tweet.keys():
            for included_tweet in tweets['includes']['tweets']:
                print(included_tweet)
                if included_tweet['id'] == tweet['referenced_tweets'][0]['id']:
                    tweet = included_tweet
                    continue

        created_at = datetime.strptime(tweet['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)

        user = users[tweet['author_id']]

        data = {
            "embeds": [{
                "author": {
                    "name": user['name'],
                    "url": f"https://www.twitter.com/{user['username']}",
                    "icon_url": user['profile_image_url']
                },
                "title": f"Tweet {tweet['id']}",
                "url": f"https://twitter.com/{user['username']}/status/{tweet['id']}",
                "description": tweet['text'],
                "color": 1940464,
                # "fields": [
                #     {
                #     "name": "Text",
                #     "value": tweet['text'],
                #     "inline": True
                #     },
                # ],
                # "image": {
                #     "url": "https://i.imgur.com/R66g1Pe.jpg",
                # },
                "footer": {
                    "text": created_at.strftime("%Y-%m-%d %H:%M:%SZ")
                }
            }]
        }

        print(json.dumps(data, indent=4))

        requests.post(os.environ['DiscordWebhook'], json=data)


def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.utcnow().replace(
        tzinfo=timezone.utc).isoformat()

    if mytimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function ran at %s', utc_timestamp)

if __name__ == '__main__':
    # tweets = json.load(open('example.json', 'r'))

    users = [
        (106554518, 1487266946928328704),
    ]

    for (user_id, since_id) in users:
        tweets = requests.get(
            f"https://api.twitter.com/2/users/{user_id}/tweets",
            params={
                "since_id": since_id,
                "expansions": "author_id,attachments.media_keys,referenced_tweets.id.author_id",
                "tweet.fields": "id,created_at,text,author_id",
                "user.fields": "name,username,profile_image_url",
                "media.fields": "height,media_key,preview_image_url,url",
            },
            headers={
                "Authorization": f"Bearer {os.environ['TwitterBearer']}"
            },
        )

        print((json.dumps(tweets.json(), indent=2)))

        tweets_to_webhooks(tweets.json())
