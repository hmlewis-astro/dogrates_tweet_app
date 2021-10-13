'''
To run this app, run `streamlit run streamlit_app.py` from inside this directory
'''
import requests
import json

import streamlit as st
# Set app title and favicon
st.set_page_config(page_title="The Underdogs",
                   page_icon="🐶",
                   layout="wide")

# Set default app width
# st.markdown(
#         f"""
# <style>
#     .reportview-container .main .block-container{{
#         max-width: 600px;
#     }}
#     .reportview-container .main {{
#         color: #000000;
#         background-color: #FFFFFF;
#     }}
# </style>
# """,
#         unsafe_allow_html=True,
#     )

import numpy as np
import pandas as pd

from pymongo import MongoClient

# Cache the function and map the type to the hash function
@st.cache(hash_funcs={MongoClient: id})
def mongo_connect(url):
    return MongoClient(url)

client = mongo_connect('mongodb://localhost:27017')

################################################################################
# Get MongoDB
#db = client.dog_rates_images

# Get 'tweets' and 'media' collections
#tweets_data = db.tweets
#tweets_media = db.media

existing_tweets = json.load(open('dog_rates_tweets.json', 'r'))
existing_tweets_media = json.load(open('dog_rates_tweets_media.json', 'r'))

# Create MongoDB with given Twitter handle
db = client[f'dog_rates_images']

# Create 'tweets' and 'media' collections
tweets_data = db.tweets
tweets_media = db.media

# Insert Tweets to collection
tweets_data.insert_many(existing_tweets)
# Insert media to collection
tweets_media.insert_many(existing_tweets_media);
################################################################################


#Display title for streamlit app
st.markdown("""
<h1 style='text-align: center;'>The Underdogs</h1>
""", unsafe_allow_html=True)

st.markdown("""
<h2 style='text-align: center;'>A compilation of the underappreciated dogs tweeted by <a href='https://twitter.com/dog_rates'>WeRateDogs</a>. 💗</h2>
""", unsafe_allow_html=True)

# Sample from Tweets with fewest favorites
pipeline = [
    {'$sort': {'favorite_count':1}},
    {'$limit':25},
    {'$sample': {'size':3}}
]

tweets_list = list(tweets_data.aggregate(pipeline))

# Embed sampled Tweets using publish.twitter.com API
cols_list = st.columns(3)

for i,tweet in enumerate(tweets_list):
    tweet_url = f"https://twitter.com/dog_rates/status/{tweet['id']}"
    embed_api = f"https://publish.twitter.com/oembed?url={tweet_url}"
    text = requests.get(embed_api).json()["html"]
    index = text.find('"twitter-tweet"') + len('"twitter-tweet"')
    text_conversation_off = text[:index] + ' data-conversation="none"' + text[index:]
    with cols_list[i]:
        st.components.v1.html(text_conversation_off, height=810)
################################################################################


# Function to format breed names list
def split_breed_name(name):
    name = name.split('-')[1].split('_')
    name = ' '.join(name)
    return name.title()

# Load data to get breed names
with open('breed_name.csv', 'r') as f:
    names = f.read().split('\n')

names = sorted(list(map(split_breed_name, names)))

st.markdown("""
<h2 style='text-align: center;'>View Tweets featuring dogs of a specific breed.</h2>
""", unsafe_allow_html=True)

default = int(np.random.choice([4, 8, 11, 13, 16, 19, 33, 39, 43, 46, 49, 67, 75, 79, 106, 115]))
# Select breed from drop-down
option = st.selectbox('Select breed:',
                      names,
                      index=default)

# Get list of Tweets where selected breed is most likely breed from the classification model
tweets_list = list(tweets_data.find({'predicted_breed.breed': {'$all': [option]}}))

if len(tweets_list) > 0:
    weights = []
    for tweet in tweets_list:
        breed_index = tweet['predicted_breed']['breed'].index(option)
        weights.append(float(tweet['predicted_breed']['probability'][breed_index]))

    weights = np.array(weights)
    weights /= sum(weights)

    size = 3
    if len(tweets_list) < size:
        size = len(tweets_list)

    cols_list = st.columns(size)

    tweets_list = np.random.choice(tweets_list, size=size, replace=False, p=weights)

    for i,tweet in enumerate(tweets_list):
        tweet_url = f"https://twitter.com/dog_rates/status/{tweet['id']}"
        embed_api = f"https://publish.twitter.com/oembed?url={tweet_url}"
        text = requests.get(embed_api).json()["html"]
        index = text.find('"twitter-tweet"') + len('"twitter-tweet"')
        text_conversation_off = text[:index] + ' data-conversation="none"' + text[index:]
        with cols_list[i]:
            st.components.v1.html(text_conversation_off, height=810)


else:
    st.write(f"""
    #### Sorry, there aren't any Tweets featuring dogs of the {option} breed.
    #### Please select a different breed and we can show you some other good dogs! 🐶
    """)
