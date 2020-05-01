import tweepy, time, sys, os, dotenv, requests, datetime, json, pathlib
import driver
from bs4 import BeautifulSoup
from twitch import TwitchHelix
from dotenv import load_dotenv
from itertools import islice
import VideoTweet
load_dotenv()
CLIP_INTERVAL = 215940
path = 'C:/Users/dnapo/AppData/Local/Google/Chrome SxS/Application/chrome.exe'



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
    streams_iterator = client.get_top_games(page_size=30)
    i=1
    top_game={}
    for game in islice(streams_iterator, 0, 30):
        top_game[str(i)] = game['id']
        i+=1
    return top_game





def get_top_clips(client, top_game):
    top_clips={}
    today = datetime.datetime.now() - datetime.timedelta(days=30)
    spot = 1
    while len(top_clips) < 7:
        i = str(spot)
        clips_iterator = client.get_clips(game_id=top_game[i], page_size=100)
        ind = 0
        found = False
        while ind < len(clips_iterator) and (not found):
            clip = clips_iterator[ind]
            if(clip['created_at'] > today):
                top_clips[i] = clip
                found = True
            ind+=1
        spot += 1
    return top_clips


def send_new_tweet(top, api):
    for i in top:
        vid_url = find_download_url(top_clips, i)
        download_vid(vid_url)
        status = '{:s}: {:s} Views: {:,d}\n\n#TwitchTv #TopClips #{:s}'.format(top[i]['broadcaster_name'], top[i]['title'], top[i]['view_count'], top[str(i)]['broadcaster_name'])
        vid_uploader =VideoTweet.VideoTweet('twitch_clip.mp4', status)
        vid_uploader.upload_init()
        vid_uploader.upload_append()
        vid_uploader.upload_finalize()
        vid_uploader.tweet()
        time.sleep(CLIP_INTERVAL)


def find_download_url(top, i):
    url = top[i]['url']
    drive = driver.driver(path)
    drive.get_page(url)
    html = drive.get_source()
    soup = BeautifulSoup(html, features="html.parser")
    vid = soup.find_all('video')
    vid_url = vid[0].attrs['src']
    drive.close_driver()
    return vid_url


def download_vid(vid_url):
    r = requests.get(vid_url)
    with open("twitch_clip.mp4",'wb') as f: 
        f.write(r.content) 


if __name__ == "__main__":
    api = set_twitter_api(*get_twitter_env())
    client_key, client_secret = get_twitch_env()
    client = TwitchHelix(client_id=client_key)
    now = datetime.datetime.now()
    while not (now.hour == 12):
        time.sleep(30)
        now = datetime.datetime.now()

    while True:
        top_clips = get_top_clips(client, get_top_games(client))
        send_new_tweet(top_clips, api)
        
    
