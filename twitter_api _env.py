# -*- coding: utf-8 -*-
"""
Created on Fri Jun 19 13:36:08 2020



@author: nlama
"""
############## Dependencies ##########################

import pandas as pd 
from pickle import load
import datetime
import twitter
from dotenv import load_dotenv


############## FUNCTIONS ############################

def GetCurrentDate():
    
    month = str(datetime.datetime.now().month)
    day = str(datetime.datetime.now().day)
    year = str(datetime.datetime.now().year)
    
    return [month,day,year]

def SaveAsCSV(df):
    outFile = "tw_data_{0}.csv".format(date_since)
    
    df.to_csv(outFile)

def DumpDataAsPickle(data):
    from pickle import dump
    
    outFile = "tw_data_{0}.pickle".format(date_since)
    
    with open(outFile, "wb") as f:
        dump(data, f)
        
def AttemptingToSalvageLocationData(df,city,state,coord):
    answer = None
    if df[df["state_id"] == city].count().id > 0:
        a = df.loc[(df["state_id"] == city),coord]
        answer = a.mean()
        
    elif df[df["state_name"] == city].count().id > 0:
        a = df.loc[(df["state_name"] == city),coord]
        answer = a.mean()
        
    return answer

def ObtainCityState(row):
    city = row["City"].strip()
    state = row["State"].strip()
    return city, state
    
    
def GetGeographicInfo(row,df,met):
    '''
    Parameters
    ----------
    row : row from map_data
    df : df is the uscities.csv
    met : met must be a column name in a uscities.csv.

    Returns
    -------
    metric float: city and state metric 

    '''
    print(df,met,row)
    metric = 0
    city, state = ObtainCityState(row)
    metric = df.loc[((df['city'] == city) & (df["state_id"] == state)),met]

    if metric.count() == 0:
        metric = df.loc[((df['city'] == city) & (df["state_name"] == state)),met]
        if metric.count() == 0:
           metric = AttemptingToSalvageLocationData(df,city,state,met)
    try:
        return metric.values[0]
    except:
        return metric

    
    
def AssignColor(row,search_terms):
    colors = ["#21897e","#3ba99c","#69d1c5","#7ebce6",
              "#8980f5","#1e212b","#ffc800","#ff8427",
              "#564787","#dbcbd8","#562c2c","#f2542d",
'#e6194B', '#3cb44b', '#ffe119', '#4363d8', '#f58231', 
'#911eb4', '#42d4f4', '#f032e6', '#bfef45', '#fabed4', 
'#469990', '#dcbeff', '#9A6324', '#fffac8', '#800000', 
'#aaffc3', '#808000', '#ffd8b1', '#000075', '#000000',
"#21897e","#3ba99c","#69d1c5","#7ebce6",
              "#8980f5","#1e212b","#ffc800","#ff8427",
              "#564787","#dbcbd8","#562c2c","#f2542d",
'#e6194B', '#3cb44b', '#ffe119', '#4363d8', '#f58231', 
'#911eb4', '#42d4f4', '#f032e6', '#bfef45', '#fabed4', 
'#469990', '#dcbeff', '#9A6324', '#fffac8', '#800000', 
'#aaffc3', '#808000', '#ffd8b1', '#000075', '#000000']

    ht = row.Hashtag.strip()
    for x in range(len(search_terms)):
        if ht == search_terms[x]:
            return colors[x]
        
def AddLongLatColorColumns(map_data):
    longLat = pd.read_csv("uscities.csv")
    map_data["Lat"] = map_data.apply(lambda row: GetGeographicInfo(row,longLat,"lat"), axis=1)
    map_data["Lng"] = map_data.apply(lambda row: GetGeographicInfo(row,longLat,"lng"), axis=1)
    map_data["Color"] = map_data.apply(lambda row: AssignColor(row,search_terms), axis=1)
    map_data["Density"] = map_data.apply(lambda row: GetGeographicInfo(row,longLat,"density"), axis=1)
    map_data["Population"] = map_data.apply(lambda row: GetGeographicInfo(row,longLat,"population"), axis=1)
    map_data_filt = map_data[map_data['Lat'].notnull()]
    
    return map_data_filt

def ObtainTweets(search_terms, date_since, count, until=None, dumpData = False):
    
    api = twitter.Api(consumer_key=CONSUMER_KEY,
                  consumer_secret=CONSUMER_SECRET,
                  access_token_key=ACCESS_TOKEN_KEY,
                  access_token_secret=ACCESS_TOKEN_SECRET)

    for term in search_terms:
        tweets = api.GetSearch(term = term, since=date_since, count=count, until=until)
        users_t = set()
        for tweet in tweets:
            loc = tweet.user.location
            locs = loc.split(",")
            us = tweet.user.name
            ca = tweet.created_at
            if len(locs) > 1 and us not in users_t:
                city.append(locs[0])
                state.append(locs[1])
                hashtag.append(term)
                date_created.append(ca)
                users_t.add(us)
        
    map_data = pd.DataFrame(list(zip(city,state,hashtag,date_created)), columns=["City", "State", "Hashtag", "Created_At"])   
    map_data = AddLongLatColorColumns(map_data)
    count_data = map_data.groupby(["City","Hashtag"]).Hashtag.transform("count")
    map_data["Counts"] = count_data
    
    if dumpData == True:
        DumpDataAsPickle(map_data)
        
    return map_data
    
def PlotOnGeo(map_data):
    
    # 1. Draw the map background
    from mpl_toolkits.basemap import Basemap
    import matplotlib.pyplot as plt
    import numpy as np
    
    fig = plt.figure(figsize=(18, 18))
    m = Basemap(projection='lcc', resolution='c', 
                lat_0=38.7596, lon_0=-88.0193,
                width=7.0E6, height=3.5E6)
    m.shadedrelief()
    m.drawcoastlines(color='gray')
    m.drawcountries(color='gray')
    m.drawstates(color='gray')
    
    
    for ht in search_terms:
        df = map_data[map_data["Hashtag"]==ht]
        lat = df['Lat'].values
        lon = df['Lng'].values
        color = df['Color'].values[0]
        m.scatter(lon, lat, c=color, s=500, cmap=plt.cm.jet, label=ht, 
                   alpha=0.5, edgecolors='none', zorder=3, latlon=True)
    plt.legend()
        
    plt.title("Geo-position of Hashtags")
    
    plt.clim(3, 7)

############################################################################
#######################
## CODE STARTS HERE! ##
##                   ##
#######################


# Define all necessary variables

# search_terms = ["#MWGA","#onlyfans", "Feminazi","#Feminism", 
#                 "#Equality","#BLM","#MAGA", "#ProChoice","#ProLife", 
#                 "#BlueLivesMurder","#DisarmthePolice","BlackLivesMatter", 
#                 "#WhiteLivesMatter", "#redpill", "AllLivesMatter",
#                 "#COVID19", "#masculinity", "#Republican", "#Democrat",
#                 "#TulsaTrumpRally","#policereforms", "#blackconservative",
#                 "#AbortionIsMurder","#DreamersAreAmericans", "#LGBTQRights",
#                 "#AbortionIsRacist","#coronavirusInSA", "#IllegalAliens",
#                 "#Copslivesmatter"]
search_terms = ["#COVID-19", "#Coronavirus", "#PPE", "#Masks"]
date = GetCurrentDate()
date_since = "{0}-{1}-{2}".format(date[2],date[0],date[1])
date_since = "2020-08-20"
count = 2000 #I just want as much as possible
# until = "{0}-{1}-{2}".format(date[2],date[0],date[1])
until = None
until = "2020-06-17"

city = []
state = []
date_created = []
hashtag = []


#If data has already been collected, just load it in. If not, collect data
#using Twitter API

# try:
#     fileName = "tw_data_{0}_{1}_{2}.pickle".format(date[0],date[1],date[2])
#     with open(fileName, "rb") as f:
#         map_data = load(f)
#         print("Loaded data from pickle")
# except:
print("Calling Twitter API ...")
# Scrape Tweets 
map_data = ObtainTweets(search_terms, date_since, count, until=until, dumpData = True)
SaveAsCSV(map_data)


print(map_data.head())

################# PLOTTING BASE MAP + TWEET LOCATIONS #####################















