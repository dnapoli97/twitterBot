import tweepy, time, sys, os, dotenv, requests, datetime
from twitch import TwitchHelix
from dotenv import load_dotenv
from itertools import islice
load_dotenv()
INTERVAL = 60*60

def get_twitter_env():    
    consumer_key = os.environ['CONSUMER_KEY']
    consumer_secret = os.environ['CONSUMER_SECRET']
    access_key = os.environ['ACCESS_KEY']
    access_secret = os.environ['ACCESS_SECRET']
    return consumer_key, consumer_secret, access_key, access_secret


def get_twitch_env():
    client_key = os.environ['CLIENT_ID']
    client_secret = os.environ['CLIENT_SECRET']
    return client_key, client_secret


def set_twitter_api(consumer_key, consumer_secret, access_key, access_secret):
    twitter_auth = tweepy.OAuthHandler(consumer_key,consumer_secret)
    twitter_auth.set_access_token(access_key,access_secret)
    twitter_api = tweepy.API(twitter_auth)
    return twitter_api


def get_top_streams(client):
    streams_iterator = client.get_streams(page_size=7)
    i=1
    top={}
    for stream in islice(streams_iterator, 0, 7):
        userName = stream['user_name']
        viewers = stream['viewer_count']
        top[str(i)] = (str(i)+'. ' + userName + ' Viewers: ' + '{:,d}').format(viewers)
        i+=1
    return top


def send_new_tweet(top, api):
    tweet = '{}\n{}\n{}\n{}\n{}\n{}\n{}\n#TwitchTv #TopStreams'.format(top['1'],top['2'],top['3'],top['4'],top['5'],top['6'],top['7'])
    api.update_status(tweet)


if __name__ == "__main__":
    api = set_twitter_api(*get_twitter_env())
    client_key, client_secret = get_twitch_env()
    client = TwitchHelix(client_id=client_key)
    now = datetime.datetime.now()
    while now.minute != 0:
        time.sleep(15)
        now = datetime.datetime.now()

    while True:
        send_new_tweet(get_top_streams(client), api)
        time.sleep(INTERVAL)


