import streamlit as st
import numpy as np
import pandas as pd
import requests
import bs4 as bs
import re
import csv
from stqdm import stqdm

baseUrl = "https://fbref.com"

euroUrl = "https://fbref.com/en/comps/676/UEFA-Euro-Stats"

r = requests.get(euroUrl)
sp = bs.BeautifulSoup(r.text, 'lxml')
tb = sp.find_all("table")[7]
countryNames = [""]
countrySquads = [""]
for row in tb.find_all("tr")[1:]:
    col = row.find_all("td")
    countryNames.append(' '.join(col[0].text.split(' ')[1:]))
    countrySquads.append(col[0].find("a")["href"])
st.title('fobol')

display = countryNames

options = list(range(len(display)))

value = st.selectbox("Team", options, format_func=lambda x: display[x])

seasons = st.slider('Seasons', min_value=1, max_value=6, value=1, step=1)


def getDataForTeam(squad,seasons):
    latest_iteration = st.empty()
    bar = st.progress(0)
    #print(tensorflow.__version__)
    yearfrom = "2021"
    yearto = "2020"

    matches = []
    st.write("["+baseUrl+countrySquads[value]+"]"+"("+baseUrl+countrySquads[value]+")")

    for season in stqdm(range(seasons)):
        #starturl = "/en/squads/29a4e4af/"+yearfrom+"-"+yearto+"/Denmark-Stats"
        urlParts = squad.split("/")
        print(urlParts)
        starturl = squad.replace(urlParts[-1],"")+"/"+yearfrom+"/"+urlParts[-1]
        print(starturl)
        yearto = str(int(yearto)-1)
        yearfrom = str(int(yearfrom)-1)
        scorers = []
        recentCards = []
        try:
            r = requests.get(baseUrl+starturl)
            sp = bs.BeautifulSoup(r.text, 'lxml')
            tb = sp.find_all('table')[1] 
            header = tb.find('thead')
            headerRow = header.find('tr')
            datecolumn = 0
            i =0
            venueColumnIndex = 0
            for th in headerRow.find_all('th'):
                print(th.text)
                if(th.text == "Venue"):
                    print("found")
                    venueColumnIndex = i-1
               
                i+=1
        except Exception as e:
                    print("Data not found")
                    #st.write(e)
        for row in stqdm(tb.find_all("tr")[1:]):
            
            try:
                col = row.find_all("td") 
                date = row.find('th').text
                venueInt = 0 if col[venueColumnIndex].text == "Home" else 1
                venueLetter = "a" if col[venueColumnIndex].text == "Home" else "b"
                venue = col[venueColumnIndex].text
                print(col[-2].find('a', href=True)['href'])
                rMatch = requests.get(baseUrl+col[-2].find('a', href=True)['href'])
                sp = bs.BeautifulSoup(rMatch.text, 'lxml')
                scores = sp.find_all('div',{"class":"score"})
                cards = sp.find_all('div',{"class":"cards"})
                searchedTeam = countryNames[value]
                opponentTeam = "Opponent"


                goalers = sp.find("div",{"id":venueLetter})
                players = goalers.find_all('div')
            
                for player in players:
                    if len(player.find_all("div",{"class":"event_icon goal"}))>0 or len(player.find_all("div",{"class":"event_icon penalty_goal"}))>0:
                        scorers.append(player.text.split('·')[0]+"-- "+date+"\r\n")

                lineup = sp.find_all("div",{"class":"lineup","id":venueLetter})[0]
                for player in lineup.find_all('tr'):
                    if len(player.find_all("div",{"class":"event_icon yellow_card"}))>0:

                        print(player.find_all("td")[1].find('a').text)
                        text = player.find_all("td")[1].find('a').text
                        if text != "":
                            recentCards.append(text + "(Y) "+ "-- "+date+"\n")
                    if len(player.find_all("div",{"class":"event_icon red"}))>0:
                        text = player.find_all("td")[1].find('a').text
                        if text != "":
                            recentCards.append(text + "(R) "+ "-- "+date+"\n")
                stats = sp.find('div',id="team_stats_extra")
                statsdiv = stats.find_all('div')
                teams = stats.find_all('div',{"class":"th"})
                
                obj = {
                    "date":date,
                    "opponent":"",
                    "goals"+searchedTeam:"",
                    "goals"+opponentTeam:"",
                    "goalsTotal":"",
                    "cards"+searchedTeam:"",
                    "cards"+opponentTeam:"",
                    "cardsTotal":"",
                    "corners"+searchedTeam:"",
                    "corners"+opponentTeam:"",
                    "cornersTotal":"",
                    #"throwInsHome":"",
                    #"throwInsAway":"",
                    #"throwInsTotal":"",
                    "fouls"+searchedTeam:"",
                    "fouls"+opponentTeam:"",
                    "foulsTotal":"",
                    "venue":venue
                }
                
                if(venueInt == 0):
                    obj["opponent"] = teams[2].text
                else:
                    if(teams[0].text != searchedTeam):
                        obj["opponent"] = teams[0].text
                    else:
                        obj["opponent"] = teams[2].text
 
            
                obj["goals"+searchedTeam] = int(scores[venueInt].text)
                obj["goals"+opponentTeam] = int(scores[1-venueInt].text)
                obj["goalsTotal"] = obj["goals"+searchedTeam] + obj["goals"+opponentTeam]
                obj["cards"+searchedTeam] = len(cards[0])
                obj["cards"+opponentTeam] = len(cards[1])
                obj["cardsTotal"] = obj["cards"+searchedTeam] +obj["cards"+opponentTeam]

                
                #obj["homeTeam"] = teams[0].text
                #obj["awayTeam"] = teams[2].text

                
                for div in range(len(statsdiv)):
                    if statsdiv[div].text == "Corners":
                        obj["corners"+searchedTeam] = int(statsdiv[div-1].text)
                        obj["corners"+opponentTeam] = int(statsdiv[div+1].text)
                        obj["cornersTotal"] =  obj["corners"+searchedTeam]+obj["corners"+opponentTeam] 
                    # elif statsdiv[div].text == "Throw Ins":
                    #     obj["throwInsHome"] = int(statsdiv[div-1].text)
                    #     obj["throwInsAway"] = int(statsdiv[div+1].text)
                    #     obj["throwInsTotal"] = obj["throwInsHome"] +obj["throwInsAway"]
                    elif statsdiv[div].text == "Fouls":
                        obj["fouls"+searchedTeam] = int(statsdiv[div-1].text)
                        obj["fouls"+opponentTeam] = int(statsdiv[div+1].text)
                        obj["foulsTotal"] = obj["fouls"+searchedTeam]+obj["fouls"+opponentTeam]
                matches.append(obj)
            except Exception as e:
                #st.write(e)
                print(e)

    footer = []
    obj = {}


    obj["opponent"] = "Average per game"
    df = pd.DataFrame(matches)
    obj["goals"+searchedTeam] = df["goals"+searchedTeam].mean()
    obj["goals"+opponentTeam] = df["goals"+opponentTeam] .mean()
    obj["goalsTotal"] = df["goalsTotal"].mean()
    obj["cards"+opponentTeam] = df["cards"+opponentTeam] .mean()
    obj["cards"+searchedTeam] = df["cards"+searchedTeam].mean()
    obj["cardsTotal"] = df["cardsTotal"].mean()
    obj["corners"+searchedTeam] = df["corners"+searchedTeam].mean()
    obj["corners"+opponentTeam] = df["corners"+opponentTeam] .mean()
    obj["cornersTotal"] = df["cornersTotal"].mean()
    obj["fouls"+searchedTeam] = df["fouls"+searchedTeam].mean()
    obj["fouls"+opponentTeam] = df["fouls"+opponentTeam] .mean()
    obj["foulsTotal"] = df["foulsTotal"].mean()



    obj2 = {}
   

    obj2["opponent"] = "Total ("+str(len(matches))+" games)"
    df = pd.DataFrame(matches)
    obj2["goals"+searchedTeam] = df["goals"+searchedTeam].sum()
    obj2["goals"+opponentTeam] = df["goals"+opponentTeam] .sum()
    obj2["goalsTotal"] = df["goalsTotal"].sum()
    obj2["cards"+searchedTeam] = df["cards"+searchedTeam].sum()
    obj2["cards"+opponentTeam] = df["cards"+opponentTeam] .sum()
    obj2["cardsTotal"] = df["cardsTotal"].sum()
    obj2["corners"+searchedTeam] = df["corners"+searchedTeam].sum()
    obj2["corners"+opponentTeam] = df["corners"+opponentTeam] .sum()
    obj2["cornersTotal"] = df["cornersTotal"].sum()
    obj2["fouls"+searchedTeam] = df["fouls"+searchedTeam].sum()
    obj2["fouls"+opponentTeam] = df["fouls"+opponentTeam].sum()
    obj2["foulsTotal"] = df["foulsTotal"].sum()


    footer.append(obj2)
    footer.append(obj)

    df2 = pd.DataFrame(footer)
   
    st.subheader("Summary")
    st.write(df2)
    st.subheader("Matches")
    df.sort_values(by=['date'], inplace=True,ascending=False)

    st.write(df)
    scorers.sort(key=lambda x: x.split( " -- ")[1].replace("-",""), reverse=True)

    st.sidebar.subheader("Recent goals:")
    st.sidebar.text(''.join(scorers[:10]))

    recentCards.sort(key=lambda x: x.split( " -- ")[1].replace("-",""), reverse=True)

    st.sidebar.subheader("Recent cards:")
    st.sidebar.text(''.join(recentCards[:10]))



if(value>0):
    getDataForTeam(countrySquads[value],seasons)





