#Sentiment Analysis
# Import Libraries
from textblob import TextBlob
import sys
import tweepy
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import nltk
import pycountry
import re
import string
from wordcloud import WordCloud, STOPWORDS
from PIL import Image
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from langdetect import detect
from nltk.stem import SnowballStemmer
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import CountVectorizer
from dotenv import load_dotenv
from pymongo import MongoClient

# import nltk
# nltk.download('vader_lexicon')

#establing connection
try:
    connect = MongoClient()
    print("Connected successfully!!!")
except:
    print("Could not connect to MongoDB")

# connecting or switching to the database
db = connect.wordCloud

# creating or switching to demoCollection
collection = db.wordCloudCollection

# import access Twitter API from .env
load_dotenv()

# Variables that contains the user credentials to access Twitter API 
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
ACCESS_SECRET = os.getenv('ACCESS_SECRET')
CONSUMER_KEY = os.getenv('CONSUMER_KEY')
CONSUMER_SECRET = os.getenv('CONSUMER_SECRET')

# Setup tweepy to authenticate with Twitter credentials:
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

# Create the api to connect to twitter with your creadentials
api = tweepy.API(auth)

#Convert decimal into percentage
def percentage(part,whole):
    return 100 * float(part)/float(whole)

#Sentimental Analysis 
def inputkeyword(keyword, noOfTweet, select) :
   #input
   tweets = tweepy.Cursor(api.search_tweets, q=keyword).items(noOfTweet)
   positive = 0
   negative = 0
   neutral = 0
   polarity = 0
   tweet_list = []
   neutral_list = []
   negative_list = []
   positive_list = []

   #for loop to query data 
   for tweet in tweets:
      #print(tweet.text)
      tweet_list.append(tweet.text)
      analysis = TextBlob(tweet.text)
      score = SentimentIntensityAnalyzer().polarity_scores(tweet.text)
      neg = score['neg']
      neu = score['neu']
      pos = score['pos']
      comp = score['compound']
      polarity += analysis.sentiment.polarity
      
      if neg > pos:
         negative_list.append(tweet.text)
         negative += 1
      elif pos > neg:
         positive_list.append(tweet.text)
         positive += 1
      elif pos == neg:
         neutral_list.append(tweet.text)
         neutral += 1

   #out of for loop : convert decimal into percentage
   positive = percentage(positive, noOfTweet)
   negative = percentage(negative, noOfTweet)
   neutral = percentage(neutral, noOfTweet)
   polarity = percentage(polarity, noOfTweet)
   positive = format(positive, '.1f')
   negative = format(negative, '.1f')
   neutral = format(neutral, '.1f')
   print(tweet._json)

   #query previous data
   exist_data = collection.find()

   #delete previous data in the storage 
   if exist_data != None :
      print("delete prvious data successfull")
      collection.delete_many({})
   
   # Inserting data to local storage one by one
   collection.insert_one(tweet._json)

   #Number of Tweets (Total, Positive, Negative, Neutral)
   tweet_list = pd.DataFrame(tweet_list)
   neutral_list = pd.DataFrame(neutral_list)
   negative_list = pd.DataFrame(negative_list)
   positive_list = pd.DataFrame(positive_list)
   print("total number: ",len(tweet_list))
   print("positive number:",len(positive_list))
   print("negative number: ", len(negative_list))
   print("neutral number: ",len(neutral_list))

   #Creating new dataframe and new features
   tw_list = pd.DataFrame(tweet_list)
   tw_list["text"] = tw_list[0]
   # print(tw_list)

   #Removing RT, Punctuation etc
   remove_rt = lambda x: re.sub('RT @\w+: '," ",x)
   rt = lambda x: re.sub("(@[A-Za-z0–9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)"," ",x)
   tw_list["text"] = tw_list.text.map(remove_rt).map(rt)
   tw_list["text"] = tw_list.text.str.lower()
   tw_list.head(10)

   #Calculating Negative, Positive, Neutral and Compound values
   tw_list[['polarity', 'subjectivity']] = tw_list['text'].apply(lambda Text: pd.Series(TextBlob(Text).sentiment))
   for index, row in tw_list['text'].items():
      score = SentimentIntensityAnalyzer().polarity_scores(row)
      neg = score['neg']
      neu = score['neu']
      pos = score['pos']
      comp = score['compound']
      if neg > pos:
         tw_list.loc[index, 'sentiment'] = "negative"
      elif pos > neg:
         tw_list.loc[index, 'sentiment'] = "positive"
      else:
         tw_list.loc[index, 'sentiment'] = "neutral"
      tw_list.loc[index, 'neg'] = neg
      tw_list.loc[index, 'neu'] = neu
      tw_list.loc[index, 'pos'] = pos
      tw_list.loc[index, 'compound'] = comp
   tw_list.head(10)

   #Creating new data frames for all sentiments (positive, negative and neutral)
   tw_list_negative = tw_list[tw_list["sentiment"]=="negative"]
   tw_list_positive = tw_list[tw_list["sentiment"]=="positive"]
   tw_list_neutral = tw_list[tw_list["sentiment"]=="neutral"]

   #count value 
   def count_values_in_column(data,feature):
      total=data.loc[:,feature].value_counts(dropna=False)
      percentage=round(data.loc[:,feature].value_counts(dropna=False,normalize=True)*100,2)
      return pd.concat([total,percentage],axis=1,keys=['Total','Percentage'])

   #Count_values for sentiment
   count_values_in_column(tw_list,"sentiment")

   #Function to Create Wordcloud for all tweet
   def create_wordcloud(text):
      mask = np.array(Image.open("mask/bird.png"))
      stopwords = set(STOPWORDS)
      wc = WordCloud(background_color= "white",mask = mask,max_words=3000,stopwords=stopwords,repeat=True)
      wc.generate(str(text))
      wc.to_file("templates/result/wc-all.png")
      print("Word Cloud Saved Successfully")
      #path="templates/result/wc-all.png"

   #Function to Create Wordcloud for all Positive tweet
   def create_wordcloud_pos(text):
      mask = np.array(Image.open("mask/bird.png"))
      stopwords = set(STOPWORDS)
      wc = WordCloud(background_color= "white",mask = mask,max_words=3000,stopwords=stopwords,repeat=True)
      wc.generate(str(text))
      wc.to_file("templates/result/wc-pos.png")
      print("Word Cloud Saved Successfully")
      #path="templates/result/wc-pos.png"

   #Function to Create Wordcloud for all Negative tweet
   def create_wordcloud_neg(text):
      mask = np.array(Image.open("mask/bird.png"))
      stopwords = set(STOPWORDS)
      wc = WordCloud(background_color= "white",mask = mask,max_words=3000,stopwords=stopwords,repeat=True)
      wc.generate(str(text))
      wc.to_file("templates/result/wc-neg.png")
      print("Word Cloud Saved Successfully")
      #path="templates/result/wc-neg.png"

    #Function to Create Wordcloud for all Neutual tweet
   def create_wordcloud_neu(text):
      mask = np.array(Image.open("mask/bird.png"))
      stopwords = set(STOPWORDS)
      wc = WordCloud(background_color= "white",mask = mask,max_words=3000,stopwords=stopwords,repeat=True)
      wc.generate(str(text))
      wc.to_file("templates/result/wc-neu.png")
      print("Word Cloud Saved Successfully")
      #path="templates/result/wc-neu.png"

   #Creating wordcloud

   #Creating wordcloud for positive sentiment
   if select == 1:
      create_wordcloud_pos(tw_list_positive["text"].values)

   #Creating wordcloud for negative sentiment
   elif select == 2:
      create_wordcloud_neg(tw_list_negative["text"].values)

   #Creating wordcloud for neutral sentiment
   elif select == 3:
      create_wordcloud_neu(tw_list_neutral["text"].values)

   #Creating wordcloud for all tweets
   elif select == 4:
      create_wordcloud(tw_list["text"].values)

   #Calculating tweet’s lenght and word count
   tw_list['text_len'] = tw_list['text'].astype(str).apply(len)
   tw_list['text_word_count'] = tw_list['text'].apply(lambda x: len(str(x).split()))
   round(pd.DataFrame(tw_list.groupby("sentiment").text_len.mean()),2)
   return 

#input from user 
keyword = input("Please enter keyword or hashtag to search: ")
noOfTweet = int(input ("Please enter how many tweets to analyze: "))
select = int(input("Please enter 1 Positive | 2 Negative | 3 Neutral | 4 All : "))
inputkeyword(keyword, noOfTweet, select) 