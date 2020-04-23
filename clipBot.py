import tweepy, time, sys, os, dotenv, requests, datetime, json, pathlib
from twitch import TwitchHelix
from dotenv import load_dotenv
from itertools import islice
load_dotenv()
CLIP_INTERVAL = 60*30
jsonClipPath = pathlib.Path('tweetedClips.json').parent.absolute().as_posix() + '/tweetedClips.json'


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
    streams_iterator = client.get_top_games(page_size=10)
    i=1
    top_game={}
    for game in islice(streams_iterator, 0, 10):
        top_game[str(i)] = game['id']
        i+=1
    return top_game


def get_top_clips(client, top_game):
    top_clips={}
    today = datetime.datetime.now() - datetime.timedelta(days=30)
    tweeted_clips = get_tweeted_clips(jsonClipPath)
    added_clips = {}
    for i in top_game:
        clips_iterator = client.get_clips(game_id=top_game[i], page_size=100)
        clip_list = []
        ind = 0
        while len(clip_list) < 5 and ind < len(clips_iterator):
            clip = clips_iterator[ind]
            if(clip['created_at'] > today) and not clip['video_id'] in tweeted_clips:
                clip_list.append(clip)
                added_clips[clip['video_id']] = {'video_id': clip['video_id'], 'title': clip['title']}
            ind+=1
        top_clips[i] = clip_list
    append_to_json(jsonClipPath, added_clips)
    return top_clips


def append_to_json(filePath, appending_dict):
    with open(filePath, "r+") as file:
        data = json.load(file)
        data.update(appending_dict)
        file.seek(0)
        json.dump(data, file)


def get_tweeted_clips(filePath):
    with open(filePath, "r+") as file:
        data = json.load(file)
        return data


def send_new_tweet(top, api):
    i = 1
    while i <= 10:
        a = 0
        while a < len(top[str(i)]):
            api.update_status('{:s}: {:s} Views: {:,d}\n{}\n#TwitchTv #TopClips #{:s}'.format(top[str(i)][a]['broadcaster_name'], top[str(i)][a]['title'], top[str(i)][a]['view_count'], top[str(i)][a]['embed_url'] + '?tt_medium=twtr', top[str(i)][a]['broadcaster_name']))
            a+=1
            time.sleep(CLIP_INTERVAL)
        i+=1    


if __name__ == "__main__":
    api = set_twitter_api(*get_twitter_env())
    client_key, client_secret = get_twitch_env()
    client = TwitchHelix(client_id=client_key)
    top_clips = get_top_clips(client, get_top_games(client))
    now = datetime.datetime.now()
    while now.minute % 15 != 0:
        time.sleep(15)
        now = datetime.datetime.now()
        
    send_new_tweet(top_clips, api)
    


