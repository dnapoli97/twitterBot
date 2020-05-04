import tweepy, time, sys, os, dotenv, requests, datetime, json, pathlib
import driver
from bs4 import BeautifulSoup
from twitch import TwitchHelix
from dotenv import load_dotenv
from itertools import islice
import VideoTweet
load_dotenv()
CLIP_INTERVAL = 79160
path = 'C:/Users/dnapo/AppData/Local/Google/Chrome SxS/Application/chrome.exe'



class clipBot():

    def __init__(self):
        self.api = self.set_twitter_api(*self.get_twitter_env())
        self.client, self.EXPIRE = self.get_twitch_env()


    def get_twitter_env(self):    
        consumer_key = os.environ['CONSUMER_KEY']
        consumer_secret = os.environ['CONSUMER_SECRET']
        access_key = os.environ['ACCESS_KEY']
        access_secret = os.environ['ACCESS_SECRET']
        return consumer_key, consumer_secret, access_key, access_secret


    def get_twitch_env(self):
        client_key = os.environ['CLIENT_ID']
        client_secret = os.environ['CLIENT_SECRET']
        response = requests.post(url='https://id.twitch.tv/oauth2/token', params={'client_id': client_key, 'client_secret': client_secret, 'grant_type': 'client_credentials'}).content
        response = json.loads(response)
        access_token = response['access_token']
        EXPIRE = response['expires_in']
        client = TwitchHelix(client_id=client_key, oauth_token=access_token)
        return client, EXPIRE


    def set_twitter_api(self, consumer_key, consumer_secret, access_key, access_secret):
        twitter_auth = tweepy.OAuthHandler(consumer_key,consumer_secret)
        twitter_auth.set_access_token(access_key,access_secret)
        twitter_api = tweepy.API(twitter_auth)
        return twitter_api


    def get_top_games(self, client):
        streams_iterator = client.get_top_games(page_size=15)
        i=1
        top_game={}
        for game in islice(streams_iterator, 0, 30):
            top_game[str(i)] = game['id']
            i+=1
        return top_game


    def get_top_clips(self, client, top_game):
        top_clips={}
        today = datetime.datetime.now() - datetime.timedelta(days=30)
        spot = 1
        temp = 1
        while len(top_clips) < 21:
            i = str(spot)
            clips_iterator = client.get_clips(game_id=top_game[i], page_size=100)
            ind = 0
            found = 0
            while ind < len(clips_iterator) and (not found == 3):
                a = str(temp)
                clip = clips_iterator[ind]
                if(clip['created_at'] > today):
                    top_clips[a] = clip
                    found += 1
                    temp += 1
                ind+=1
            spot += 1
        return top_clips


    def send_new_tweet(self, top, api):
        daily_count = 0
        for i in top:
            vid_url = self.find_download_url(top, i)
            self.download_vid(vid_url)
            status = '{:s}: {:s} Views: {:,d}\n\n#TwitchTv #TopClips #{:s}'.format(top[i]['broadcaster_name'], top[i]['title'], top[i]['view_count'], top[str(i)]['broadcaster_name'])
            vid_uploader =VideoTweet.VideoTweet('twitch_clip.mp4', status)
            vid_uploader.upload_init()
            vid_uploader.upload_append()
            vid_uploader.upload_finalize()
            vid_uploader.tweet()
            daily_count+= 1
            if daily_count == 3:
                time.sleep(CLIP_INTERVAL)
                daily_count = 0
            else:
                time.sleep(3560)


    def find_download_url(self, top, i):
        url = top[i]['url']
        drive = driver.driver(path)
        drive.get_page(url)
        html = drive.get_source()
        soup = BeautifulSoup(html, features="html.parser")
        vid = soup.find_all('video')
        vid_url = vid[0].attrs['src']
        drive.close_driver()
        return vid_url


    def download_vid(self, vid_url):
        r = requests.get(vid_url)
        with open("twitch_clip.mp4",'wb') as f: 
            f.write(r.content) 


    def run(self):
        now = datetime.datetime.now()
        while not (now.hour == 22 and now.minute == 30):
            time.sleep(30)
            now = datetime.datetime.now()

        while True:
            if not self.EXPIRE:
                self.client, self.EXPIRE = self.get_twitch_env()
            top_clips = self.get_top_clips(self.client, self.get_top_games(self.client))
            self.send_new_tweet(top_clips, self.api)
        
    
if __name__ == "__main__":
    main = clipBot()
    main.run()

