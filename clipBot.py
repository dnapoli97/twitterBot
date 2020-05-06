import tweepy, time, sys, os, dotenv, requests, datetime, json, pathlib
import driver
from bs4 import BeautifulSoup
from twitch import TwitchHelix
from dotenv import load_dotenv
from itertools import islice
from requests import codes
import VideoTweet
load_dotenv()
CLIP_INTERVAL = 79160
path = 'C:/Users/dnapo/AppData/Local/Google/Chrome SxS/Application/chrome.exe'
json_file_name = 'top_clips.json'



class clipBot():
    _rate_limit_resets = set()
    _rate_limit_remaining = 0

    def _wait_for_rate_limit_reset(self):
        if self._rate_limit_remaining == 0:
            current_time = int(time.time())
            self._rate_limit_resets = set(x for x in self._rate_limit_resets if x > current_time)

            if len(self._rate_limit_resets) > 0:
                reset_time = list(self._rate_limit_resets)[0]

                # Calculate wait time and add 0.1s to the wait time to allow Twitch to reset
                # their counter
                wait_time = reset_time - current_time + 0.1
                time.sleep(wait_time)


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
        streams_iterator = client.get_top_games(page_size=30)
        i=1
        top_game={}
        for game in islice(streams_iterator, 0, 30):
            top_game[str(i)] = game['id']
            i+=1
        return top_game


    def get_top_clips(self, client, top_game):
        top_clips={}
        today = datetime.datetime.now(datetime.timezone.utc).astimezone() - datetime.timedelta(days=30)
        for game in top_game:
            clips_iterator = self.top_clips_api(top_game[game], 20, today.isoformat())
            for element in clips_iterator:
                top_clips[str(len(top_clips))] = element
        return {k: v for k, v in sorted(top_clips.items(), key=lambda item: item[1]['view_count'], reverse=True)}


    def top_clips_api(self, game_id, page_size, started_at):
        self._wait_for_rate_limit_reset()
        now = datetime.datetime.now(datetime.timezone.utc).astimezone()
        response = requests.get(url='https://api.twitch.tv/helix/clips', headers={'Client-ID': self.client._client_id},params={'game_id':game_id, 'first': page_size, 'started_at': started_at, 'ended_at': now.isoformat() })
        
        remaining = response.headers.get('Ratelimit-Remaining')
        if remaining:
            self._rate_limit_remaining = int(remaining)

        reset = response.headers.get('Ratelimit-Reset')
        if reset:
            self._rate_limit_resets.add(int(reset))

        # If status code is 429, re-run _request_get which will wait for the appropriate time
        # to obey the rate limit
        if response.status_code == 429:
            return self.top_clips_api(game_id, page_size, started_at)
        
        response = json.loads(response.content)
        return response['data']


    def send_new_tweet(self, top, api):
        
        for i in top:
            if self.EXPIRE < 3600:
                self.client, self.EXPIRE = self.get_twitch_env()
            now = datetime.datetime.now()
            vid_url = self.find_download_url(top, i)
            self.download_vid(vid_url)
            status = '{:s}: {:s} Views: {:,d}\n\n#TwitchTv #Twitch #TopClips #{:s}'.format(top[i]['broadcaster_name'], top[i]['title'], top[i]['view_count'], top[str(i)]['broadcaster_name'])
            vid_uploader =VideoTweet.VideoTweet('twitch_clip.mp4', status)
            vid_uploader.upload_init()
            vid_uploader.upload_append()
            vid_uploader.upload_finalize()
            vid_uploader.tweet()
            del top[i]
            self.output_to_json(top)
            time.sleep(1770)
            then = datetime.datetime.now() - now
            elapsed = then.total_seconds()
            self.EXPIRE -= elapsed


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


    def output_to_json(self, top_clips):
        position = 1
        output = {}
        for i in top_clips:
            output[str(position)] = top_clips[i]
            position += 1
            if position > 336:
                with open(json_file_name, 'w+') as jsonFlie:
                    jsonFlie.write(json.dumps(output, indent=4))
                return


    def read_from_json(self):
        try:
            with open(json_file_name, 'r+') as top_clips_file:
                top_clips = json.load(top_clips_file)
                if len(top_clips) == 0:
                    self.output_to_json(self.get_top_clips(self.client, self.get_top_games(self.client)))
                    return self.read_from_json()
                else:
                    return top_clips
        except FileNotFoundError:
            with open(json_file_name, 'w+') as file:
                file.write(json.dumps({}, indent=4))
            return self.read_from_json()


    def download_vid(self, vid_url):
        r = requests.get(vid_url)
        with open("twitch_clip.mp4",'wb') as f: 
            f.write(r.content) 


    def run(self):
        now = datetime.datetime.now()
        while not (now.minute == 15 or now.minute == 45):
            time.sleep(30)
            now = datetime.datetime.now()

        while True:
            if self.EXPIRE < 3600:
                self.client, self.EXPIRE = self.get_twitch_env()
            top_clips = self.read_from_json()
            self.output_to_json(top_clips)
            self.send_new_tweet(top_clips, self.api)
        
    
if __name__ == "__main__":
    main = clipBot()
    main.run()
