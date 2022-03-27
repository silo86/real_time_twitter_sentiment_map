import streamlit as st
import os
import pandas as pd
import tweepy
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import Stream
import nltk
from nltk.corpus import stopwords
import string
from wordcloud import WordCloud
import stylecloud
import plotly.express as px
from plotly.offline import download_plotlyjs , init_notebook_mode, plot, iplot
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from streamer import Listener
from model import myModel
from util import cleanTxt

init_notebook_mode(connected=True)
st.set_option('deprecation.showPyplotGlobalUse', False)

#variables
map_token = os.getenv('map_token')
consumer_key = os.getenv('consumer_key')
consumer_secret = os.getenv('consumer_secret')
access_token = os.getenv('access_token')
access_token_secret = os.getenv('access_token_secret')

st.markdown(
    """
    <style>
        .stProgress > div > div > div > div {
            background-image: linear-gradient(to right, #99ff99 , #00ccff);
        }
    </style>""",
    unsafe_allow_html=True,
)

#Argentina Bounding box West -77°, South -57°, East -52°, North -20°.
Argentina = [-73.48, -56.41, -53.53, -21.86]
#load pretrained BERT model
model = myModel()

st.title("Tweets sentiment map 🔥")
activities=["Usuarios","Mapa en vivo"]
choice = st.sidebar.selectbox("Elige una opcion",activities)
if choice == "Mapa en vivo":
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

    if submit_button:
        st.write('obteniendo tweets')
        progress_bar = st.progress(0)
        key = key.lower()
        myStream = Listener(consumer_key,consumer_secret,access_token,access_token_secret)
        if st.button("Cancelar"):
            pass
        tweets_list = []
        myStream.getTweetsByGPS(tweets_list, progress_bar, number, key, -73.48, -56.41, -53.53, -21.86)


        # Clean the tweets
        tweets = pd.DataFrame(myStream.tweets_list, columns=['lat','lon','text'])
        tweets['text'] = tweets['text'].apply(lambda x: cleanTxt(x))
        #predict sentiments
        tweets['sentiment'] = tweets['text'].apply(lambda x: model.predict_sentiment(x))
        st.write(tweets)
        #labeling tweets sentiments
        tweets.sentiment[tweets['sentiment'] == 1] = 'N+'
        tweets.sentiment[tweets['sentiment'] == 2] = 'N'
        tweets.sentiment[tweets['sentiment'] == 3] = 'NEU'
        tweets.sentiment[tweets['sentiment'] == 4] = 'P'
        tweets.sentiment[tweets['sentiment'] == 5] = 'P+'
    
        discrete_map = {'N+':'red','N':'orange','NEU':'yellow','P':'#90EE90','P+':'green'}
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
        choice = form.selectbox("elige la forma:",forms)
        submit_button = form.form_submit_button(label='Aceptar')

    if submit_button:
        raw_text = key
        authenticate = tweepy.OAuthHandler(consumer_key, consumer_secret) 
        # Set the access token and access token secret
        authenticate.set_access_token(access_token, access_token_secret) 
        
        api = tweepy.API(authenticate, wait_on_rate_limit = True)
        posts = api.user_timeline(screen_name=raw_text, count = 100, lang ="en", tweet_mode="extended")
        df = pd.DataFrame([tweet.full_text for tweet in posts], columns=['Tweets'])
        st.write(df.iloc[0].Tweets)

        df['Tweets'] = df['Tweets'].apply(lambda x: cleanTxt(x))

        punct = list(string.punctuation)
        punct.extend(['¿', '¡'])
        punct.extend(map(str,range(10)))
        stop_words = stopwords.words('spanish')
        def remove_stopWords(sentence):
            sentence = sentence.lower().split(' ')
            cleaned = [word for word in sentence if word not in punct and word not in stop_words]
            return cleaned
        df['Tweets'] = df['Tweets'].apply(lambda x: remove_stopWords(x))
        word_list = [word for l in df['Tweets'] for word in l]
        text = ''
        for word in word_list:
            text += ' '+str(word)
        with open("file.txt", "w") as output:
            output.write(text)
        my_stopwords = [key]
        stylecloud.gen_stylecloud(file_path='file.txt',
                                icon_name=choice,
                                palette='colorbrewer.diverging.Spectral_11',
                                #background_color='black',
                                gradient='horizontal'
        #                        ,custom_stopwords=my_stopwords
                                )
        img = mpimg.imread('stylecloud.png')
        fig, ax = plt.subplots()
        plt.axis("off")
        plt.imshow(img)
        
        st.pyplot(plt.show())

        st.write('opiniones')
        replies=[]
        coordinates = [-73.4154357571, -55.25, -53.628348965, -21.8323104794] #arg
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

       
 