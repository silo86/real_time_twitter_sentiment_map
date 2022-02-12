import streamlit as st
import pandas as pd
import json
import tweepy
import time
import matplotlib.pyplot as plt
#import seaborn as sns
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import Stream
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import re
import plotly.express as px
import streamlit as st
from plotly.offline import download_plotlyjs , init_notebook_mode, plot, iplot
#from plotly.offline import download_plotlyjs, plot, iplot

init_notebook_mode(connected=True)
st.set_option('deprecation.showPyplotGlobalUse', False)


st.markdown(
    """
    <style>
        .stProgress > div > div > div > div {
            background-image: linear-gradient(to right, #99ff99 , #00ccff);
        }
    </style>""",
    unsafe_allow_html=True,
)

consumer_key = 'VPvui5U6EquRPekMxl7vcRLd4'
consumer_secret = 'lFLlhdsr4qltTmzlNfTjtHNrYkJ1nidJvpkr0lV284bEg6i3ZI'
access_token = '2289545803-aZ3tKTWnFc9v0sDu6AjS4RMv3unLG7KalvIPhdt'
access_token_secret = 'qxoQtbsklOGDnvieXDCdwTIaRGNYN9zdXAylNPWVHduPs'

#Argentina Bounding box West -77°, South -57°, East -52°, North -20°.
Argentina = [-73.48, -56.41, -53.53, -21.86]


def predict_sentiment(text):
    token = tokenizer.encode(text, return_tensors='pt')
    result = model(token)
    result = torch.argmax(result.logits)+ 1
    return result.item()

##########################

st.title("Tweet Sentiments 🔥")
activities=["Usuarios","Mapa en vivo"]
choice = st.sidebar.selectbox("Elige una opcion",activities)
if choice == "Mapa en vivo":
    #st.title('Mapa de Tweets')
    st.subheader(
        "Busca tweets en tiempo real con un contenido determinado y analiza como la gente esta reaccionando")
    st.write('Este proceso puede tardar varios minutos, ten en cuenta que se esta filtrando por contenido y ademas por aquellos tweets que tengan las coordenadas activadas')

    form = st.form(key='my_form')
    with form:
        key = form.text_input(label='contenido')
        number = form.number_input(
            'tweets', min_value=0, max_value=10000, value=10)
        submit_button = form.form_submit_button(label='Aceptar')

    tweets = pd.DataFrame()
    tweets_list = []


    class listener(tweepy.Stream):
        tweet_counter = 0
        tcounter = 0
        def on_data(self, data):
            # Twitter returns data in JSON format - we need to decode it first
            if  listener.tweet_counter < listener.stop_at:
                listener.tcounter += 1
                print(str(listener.tcounter))
                decoded = json.loads(data)
                if decoded.get('place') is not None:
                    location = decoded.get('place').get('bounding_box').get('coordinates')[0][0]
                else:
                    location = '[,]'
                text = decoded['text'].replace('\n',' ')
                user = '@' + decoded.get('user').get('screen_name')
                created = decoded.get('created_at')
                tweet = [location[0],location[1], text]
                if listener.keyword in text.lower():
                    tweets_list.append(tweet)
                    listener.tweet_counter += 1
                    print(f' tweets encontrados: {listener.tweet_counter}')
                    my_bar.progress(listener.tweet_counter * listener.progress_bar)
                return True
            else:
                self.disconnect()
                print(f"Max number reached: {listener.tweet_counter} outputs")

        def getTweetsByHashtag(self, stop_at_number, hashtag):
            try:
                listener.stop_at = stop_at_number
                myStream.filter(track=[hashtag])
            except KeyboardInterrupt:
                print('Got keyboard interrupt')

        def getTweetsByGPS(self, stop_at_number,kword, latitude_start, longitude_start, latitude_finish, longitude_finish):
            try:
                listener.keyword = kword # Create static variable
                listener.stop_at = stop_at_number # Create static variable
                listener.progress_bar = 1/stop_at_number
                myStream.filter(follow=None, locations=[latitude_start, longitude_start, latitude_finish, longitude_finish])
            except KeyboardInterrupt:
                print('Got keyboard interrupt')
        def on_error(self, status):
            if status_code == 420:
    #returning False in on_error disconnects the stream
                return False
    # returning non-False reconnects the stream, with backoff.

    if submit_button:
        st.write('obteniendo tweets')
        my_bar = st.progress(0)
        key = key.lower()
    #    print ('Starting')
        myStream = listener(consumer_key,consumer_secret,access_token,access_token_secret)
        if st.button("Cancelar"):
            pass
        myStream.getTweetsByGPS(number,key,-73.48, -56.41, -53.53, -21.86)

        tokenizer = AutoTokenizer.from_pretrained('nlptown/bert-base-multilingual-uncased-sentiment')
        model = AutoModelForSequenceClassification.from_pretrained('nlptown/bert-base-multilingual-uncased-sentiment')

        def cleanTxt(text):
            text = re.sub('@[A-Za-z0–9]+', '', text) #Removing @mentions
            text = re.sub('#', '', text) # Removing '#' hash tag
            text = re.sub('RT[\s]+', '', text) # Removing RT
            text = re.sub('https?:\/\/\S+', '', text) # Removing hyperlink
            text = re.sub('^\d+\s|\s\d+\s|\s\d+$','',text) #Removing numbers
            return text

        # Clean the tweets
        tweets = pd.DataFrame(tweets_list, columns=['lat','lon','text'])
        tweets['text'] = tweets['text'].apply(lambda x: cleanTxt(x))
        #predict sentiments
        tweets['sentiment'] = tweets['text'].apply(lambda x: predict_sentiment(x))
    #    st.metric('tweets', len(tweets))
        st.write(tweets)
        #labeling tweets sentiments
        tweets.sentiment[tweets['sentiment'] == 1] = 'N+'
        tweets.sentiment[tweets['sentiment'] == 2] = 'N'
        tweets.sentiment[tweets['sentiment'] == 3] = 'NEU'
        tweets.sentiment[tweets['sentiment'] == 4] = 'P'
        tweets.sentiment[tweets['sentiment'] == 5] = 'P+'
    
        discrete_map = {'N+':'red','N':'orange','NEU':'yellow','P':'#90EE90','P+':'green'}
        map_token = 'pk.eyJ1IjoicHlheG9sb3RsIiwiYSI6ImNrdzNsYTJwbjZhbmkydm10c2ZjbDFxNTYifQ.2Xmyk_We9QPLJHDalapzog'
        px.set_mapbox_access_token(map_token)
        #scatter map
        fig = px.scatter_mapbox(tweets, lat=tweets['lon'], lon=tweets['lat'],  hover_data=['lat','lon','sentiment'] ,color = tweets.sentiment,color_discrete_map=discrete_map, zoom=2, center={"lat":-34.60652, "lon":-58.43557})
        st.write(fig)
        #pie chart
        counts_=tweets.value_counts()
        fig = px.pie(tweets, values=counts_, names='sentiment',color=tweets.sentiment,
                color_discrete_map=discrete_map,
                )
        st.write(fig)
else:
    st.subheader('Busca un usuario de twitter para analizar los comentarios sobre su ultimo post')
    twitter = 'fab fa-twitter'
    flag = 'fas fa-flag'
    cloud = 'fas fa-cloud'
    forms = [twitter,flag,cloud]
    form = st.form(key='my_form')
    with form:
        key = form.text_input(label='usuario de twitter:')
#        number = form.number_input(
#            'tweets', min_value=0, max_value=10000, value=10)
        choice = form.selectbox("elige la forma:",forms)
        submit_button = form.form_submit_button(label='Aceptar')
#    raw_text = 'mauriciomacri'

    if submit_button:
        raw_text = key
        authenticate = tweepy.OAuthHandler(consumer_key, consumer_secret) 
        # Set the access token and access token secret
        authenticate.set_access_token(access_token, access_token_secret) 
        
        api = tweepy.API(authenticate, wait_on_rate_limit = True)
        posts = api.user_timeline(screen_name=raw_text, count = 100, lang ="en", tweet_mode="extended")
        df = pd.DataFrame([tweet.full_text for tweet in posts], columns=['Tweets'])
        st.write(df.iloc[0].Tweets)
        def cleanTxt(text):
            text = re.sub('@[A-Za-z0–9]+', '', text) #Removing @mentions
            text = re.sub('#', '', text) # Removing '#' hash tag
            text = re.sub('RT[\s]+', '', text) # Removing RT
            text = re.sub('https?:\/\/\S+', '', text) # Removing hyperlink
            text = re.sub('^\d+\s|\s\d+\s|\s\d+$','',text) #Removing numbers
            return text
        df['Tweets'] = df['Tweets'].apply(lambda x: cleanTxt(x))
        import nltk
        from nltk.corpus import stopwords
        from wordcloud import WordCloud
        import string
        punct = list(string.punctuation)
        punct.extend(['¿', '¡'])
        punct.extend(map(str,range(10)))
        #from spacy.lang.es.stop_words import STOP_WORDS
        stop_words = stopwords.words('spanish')
    #   stop_words.extend(['El','La','Es','Todo','Este','a'])
        def remove_stopWords(sentence):
            sentence = sentence.lower().split(' ')
            cleaned = [word for word in sentence if word not in punct and word not in stop_words]
            return cleaned
        df['Tweets'] = df['Tweets'].apply(lambda x: remove_stopWords(x))
        word_list = [word for l in df['Tweets'] for word in l]
        #allWords = (' ').join(word_list)
        #wordCloud = WordCloud( max_font_size=110).generate(allWords)
        #fig, ax = plt.subplots()
        #plt.axis("off")
        #ax = plt.imshow(wordCloud, interpolation="bilinear")
        #st.pyplot(fig)
        text = ''
        for word in word_list:
            text += ' '+str(word)
        with open("file.txt", "w") as output:
            output.write(text)
        #    output.write(str(word_list))
        import stylecloud
        
        my_stopwords = [key]
        stylecloud.gen_stylecloud(file_path='file.txt',
                                icon_name=choice,
                                palette='colorbrewer.diverging.Spectral_11',
                                #background_color='black',
                                gradient='horizontal'
        #                        ,custom_stopwords=my_stopwords
                                )

        import matplotlib.image as mpimg
        img = mpimg.imread('stylecloud.png')
        fig, ax = plt.subplots()
        plt.axis("off")
        plt.imshow(img)
        
        st.pyplot(plt.show())

        st.write('opiniones')
        replies=[]
        coordinates = [-73.4154357571, -55.25, -53.628348965, -21.8323104794] #arg
        #non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)
        for full_tweets in tweepy.Cursor(api.user_timeline,geocode = coordinates,screen_name= key,tweet_mode='extended',include_rts=False,timeout=999999).items(5):
            for tweet in tweepy.Cursor(api.search_tweets,q='to:'+ key,tweet_mode='extended',result_type='recent',timeout=999999).items(100):
                if hasattr(tweet, 'in_reply_to_status_id_str'):
                    if (tweet.in_reply_to_status_id_str==full_tweets.id_str):
                        replies.append(tweet.full_text)
            print("Tweet :",full_tweets)
            for elements in replies:
                print("Replies :",elements)
        
        preprocessed_replies=[]
        for item in replies:
            preprocessed_list = remove_stopWords(cleanTxt(item.lower()))
            for item in preprocessed_list:
                preprocessed_replies.append(item)

        allWords = (' ').join(preprocessed_replies)
        wordCloud = WordCloud( max_font_size=110).generate(allWords)
        fig, ax = plt.subplots()
        plt.axis("off")
        ax = plt.imshow(wordCloud, interpolation="bilinear")
        st.pyplot(fig)

       
 