'''
To run this app, run `streamlit run streamlit_app.py` from inside this directory
'''
# Define whether working in development mode (True, i.e., localhost) or in deployment mode (False, i.e., Heroku)
dev_mode = False

import os
import requests

import streamlit as st
# Set app title and favicon
st.set_page_config(page_title="The Underdogs",
                   page_icon="🐶",
                   layout="wide")

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"""
        <style>{f.read()}</style>
        """, unsafe_allow_html=True)

local_css('style/style.css')

import numpy as np
import pandas as pd

# For deployed Streamlit app
if not dev_mode:
    import dns
    uri = os.environ['MONGODB_URI']

from pymongo import MongoClient

# Cache the function and map the type to the hash function
@st.cache(hash_funcs={MongoClient: id})
def mongo_connect(url):
    return MongoClient(url)

# For deployed app
if not dev_mode:
    client = mongo_connect(uri)

# For local app
if dev_mode:
    client = mongo_connect('mongodb://localhost:27017')

################################################################################
# Get MongoDB
db = client.dog_rates_images

# Get 'tweets' and 'media' collections
tweets_data = db.tweets
tweets_media = db.media
################################################################################


# Hide menu at top of screen
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Display title for streamlit ap
st.markdown("""
<div align='center'>
<h1 style=font-size:56px>
The Underdogs
</h1>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div align='center'>
<h2>
A compilation of underappreciated dogs tweeted by <a href='https://twitter.com/dog_rates'>WeRateDogs</a>. 💗
</h2>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<br>
<div>
The dogs highlighted here received fewer favorites than most of the dogs rated by the WeRateDogs account. We think they deserve some more love, because they're <i>all</i> good dogs.
<br>
<br>
Below, you can also view Tweets featuring dogs of your favorite breed. Just scroll down and choose a breed!
<br>
<br>
</div>
""", unsafe_allow_html=True)
################################################################################


# Sample from Tweets with fewest favorites
# Set limit based on current size of the Tweets collection
limit = tweets_data.count_documents({}) // 10

pipeline = [
    {'$sort': {'favorite_count':1}},
    {'$limit':limit},
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
<div align='center'><h2>View Tweets featuring dogs of a specific breed.</h2></div>
""", unsafe_allow_html=True)

# Select breed from drop-down
option = st.selectbox('Select breed:',
                      names,
                      index=49
                      )

# Get list of Tweets where selected breed is most likely breed from the classification model
tweets_list = list(tweets_data.find({'predicted_breed.breed': {'$all': [option]}}))

if len(tweets_list) > 0:
    weights = []
    for tweet in tweets_list:
        breed_index = tweet['predicted_breed']['breed'].index(option)
        weights.append(float(tweet['predicted_breed']['probability'][breed_index]))

    weights = (np.array(weights)*100)**2
    weights /= sum(weights)

    size = 3
    if len(tweets_list) < size:
        size = len(tweets_list)

    cols_list = st.columns(size)

    # Weight random select by probability of breed from the classification model
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
################################################################################


def info_header(text):
     st.markdown(f"""
     <p style='background-color:#D2ECFC;
               color:#14171A;
               font-size:16px;
               border-radius:2px;
               padding: 10px 18px 10px 18px;
               '>{text}</p>
     """, unsafe_allow_html=True)

info_header("""The Tweets included in this webapp are updated frequently. \
 If the Tweets shown here appear to be significantly out-of-date (e.g., all Tweets are older than 6 months) please complete the form below to notify the app developer.<br><br> \
 If you have any other concerns, questions, a bug/issue to report, or comments (positive or negative!), please also fill out the form below. The developer will be in touch if needed.<br><br>
 Thank you for your support!""")

#TODO: fix submit button colors
#<form action="https://formsubmit.co/hanlewis528@gmail.com" method="POST">
st.markdown("""
<form action="https://formsubmit.co/a0a0b3e876f618f6e89f121c34461374" method="POST">
     <input type="text" name="Name" placeholder="Your Name" required>
     <input type="email" name="Email" placeholder="Email Address" required>
     <textarea name="Comment" placeholder="Comment" required></textarea>
     <input type="text" name="_honey" style="display:none">
     <input type="hidden" name="_autoresponse" value="Your comment has been submitted to the developer of The Underdogs webapp. Thank you!">
     <input type="hidden" name="_template" value="box">
     <button type="submit">Submit</button>
</form>
""", unsafe_allow_html=True)
