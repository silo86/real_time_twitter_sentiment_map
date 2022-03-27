import tweepy
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import Stream
import json

#my_bar = st.progress(0)
#tweets_list = []
class Listener(tweepy.Stream):
        tweet_counter = 0
        tcounter = 0
        def on_data(self, data):
            # Twitter returns data in JSON format - we need to decode it first
            if  Listener.tweet_counter < Listener.stop_at:
                Listener.tcounter += 1
                print(str(Listener.tcounter))
                decoded = json.loads(data)
                if decoded.get('place') is not None:
                    location = decoded.get('place').get('bounding_box').get('coordinates')[0][0]
                else:
                    location = '[,]'
                text = decoded['text'].replace('\n',' ')
                user = '@' + decoded.get('user').get('screen_name')
                created = decoded.get('created_at')
                tweet = [location[0],location[1], text]
                if Listener.keyword in text.lower():
                    self.tweets_list.append(tweet)
                    Listener.tweet_counter += 1
                    print(f' tweets encontrados: {Listener.tweet_counter}')
                    
                    
                    self.my_bar.progress(Listener.tweet_counter * Listener.progress_bar)
                return True
            else:
                print(f"Max number reached: {Listener.tweet_counter} outputs")
                self.disconnect()
                return self.tweets_list
                

        def getTweetsByHashtag(self, stop_at_number, hashtag):
            try:
                Listener.stop_at = stop_at_number
                Listener.filter(self,track=[hashtag])
            except KeyboardInterrupt:
                print('Got keyboard interrupt')

        def getTweetsByGPS(self, lista, my_bar, stop_at_number,kword, latitude_start, longitude_start, latitude_finish, longitude_finish):
            try:
                Listener.tweets_list = lista
                Listener.my_bar = my_bar
                Listener.keyword = kword # Create static variable
                Listener.stop_at = stop_at_number # Create static variable
                Listener.progress_bar = 1/stop_at_number
                Listener.filter(self, follow=None, locations=[latitude_start, longitude_start, latitude_finish, longitude_finish])
            except KeyboardInterrupt:
                print('Got keyboard interrupt')
        def on_error(self, status):
            if status_code == 420:
    #returning False in on_error disconnects the stream
                return False
    # returning non-False reconnects the stream, with backoff.