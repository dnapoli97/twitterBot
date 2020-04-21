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


def get_top_games(client):
    streams_iterator = client.get_top_games(page_size=20)
    i=1
    top_game={}
    for game in islice(streams_iterator, 0, 20):
        top_game[str(i)] = game['id']
        i+=1
    return top_game


def get_top_clips(client, top_game):
    top_clips={}
    for i in top_game:
        clips_iterator = client.get_clips(game_id=top_game[i], page_size=5)
        clip_list = []
        for clip in islice(clips_iterator, 0, 5):
            clip_list.append(clip)
        top_clips[i] = clip_list
    return top_clips
    

def send_new_tweet(top, api):
    print(top)
    

if __name__ == "__main__":
    api = set_twitter_api(*get_twitter_env())
    client_key, client_secret = get_twitch_env()
    client = TwitchHelix(client_id=client_key)
    send_new_tweet(get_top_clips(client, get_top_games(client)), api)
    now = datetime.datetime.now()
    #while now.minute != 0:
        #now = datetime.datetime.now()
        #time.sleep(15)

    #while True:
        #send_new_tweet(get_top_streams(client), api)
        #time.sleep(INTERVAL)


