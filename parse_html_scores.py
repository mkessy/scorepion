#Functions to pull MLB scores from the ESPN website and output them in JSON format


import re
import urllib2, urllib
import lxml
from bs4 import BeautifulSoup, SoupStrainer
from bs4.diagnose import diagnose
import simplejson as json
import timeit, time
import pprint


def pull_game_ids(mlb_soup):
    """Given an mlbSoup returns two dicts of game IDs, the first is AL games, the second is NL games"""
    AL = {}
    NL = {}

    al= mlb_soup.find(id='gamesLeft-1')
    nl= mlb_soup.find(id='gamesRight-1')

    al = al.find_all(id=re.compile(r'[0-9]+-gamebox'))
    nl = nl.find_all(id=re.compile(r'[0-9]+-gamebox'))

    def classify_game(tag):
        if 'in-game' in tag['class']:
            return 'in_game'
        elif 'preview' in tag['class']:
            return 'preview'
        elif 'final-state' in tag['class']:
            return 'final'

    AL = {tag['id'].split('-')[0]:classify_game(tag) for tag in al}
    NL = {tag['id'].split('-')[0]:classify_game(tag) for tag in nl}

    return AL, NL


def pull_team_names(mlbSoup, gameID, dataDict):
    """
    Away team name HTML - this is the same for home team with the a in 'aTeamName' replaced by an h
    <span id="330606106-aTeamName"><a href="http://espn.go.com/mlb/team/_/name/tb/tampa-bay-rays">Rays</a></span>
    """
    aTeamName = mlbSoup.find('span', id=gameID+"-aTeamName")
    hTeamName = mlbSoup.find('span', id=gameID+"-hTeamName")

    if aTeamName and hTeamName:
        dataDict['away_team'] = unicode(aTeamName.contents[0].string)
        dataDict['home_team'] = unicode(hTeamName.contents[0].string)


def pull_team_records(mlbSoup, gameID, dataDict):
    """
    #Team records
    #<p id="330606118-aRecord" class="record">(33-26, 18-13 away)</p>
    """
    def format_record(rec):
        return rec.strip('()').replace(',','').split()[:-1]

    aRecord = mlbSoup.find('p', id=gameID+"-aRecord", class_="record")
    if aRecord:
        dataDict['away_record'] = unicode(aRecord.string)
    hRecord = mlbSoup.find('p', id=gameID+"-hRecord", class_="record")
    if hRecord:
        dataDict['home_record'] = unicode(hRecord.string)



def pull_team_starters(mlbSoup, gameID, dataDict):
    """
    home and away starters
    <div id="330607114-awayStarter" class="border-top game-info-module" style="display: block; padding-bottom: 0px;">
       <strong>TEX:&nbsp;&nbsp;&nbsp;</strong>
        <a href="http://espn.go.com/mlb/player/_/id/32700/nick-tepesch">Tepesch</a>
        (3-4, 3.44 ERA)
    </div>
    """

    aStarter = mlbSoup.find('div', id=gameID+"-awayStarter")
    if aStarter:
        dataDict['away_starter'] = map(unicode,
                                    (aStarter.contents[1].string,
                                     aStarter.contents[2]))

    hStarter = mlbSoup.find('div', id=gameID+"-homeStarter")
    if hStarter:
        dataDict['home_starter'] = map(unicode,
                                    (hStarter.contents[1].string,
                                     hStarter.contents[2]))


def pull_game_status(mlbSoup, gameID, dataDict):
    """
    Current game status
    <p id="330606106-statusLine1">Top 9th</p>
    """
    gameStatus = mlbSoup.find('p', id=gameID+"-statusLine1")
    if gameStatus:
        dataDict['game_status'] = unicode(gameStatus.string)


def pull_game_note(mlbSoup, gameID, dataDict):
    """
    <div id="330606120-gameNote" class="border-top game-info-module" style="display: block;">
        THE GAME HAS BEEN POSTPONED DUE TO RAIN. NO MAKEUP DATE HAS BEEN ANNOUNCED.
    </div>
    """

    gameNote = mlbSoup.find('div', id=gameID+"-gameNote")
    if gameNote:
        dataDict['game_note'] = unicode(gameNote.string)


def pull_game_scores(mlbSoup, gameID, dataDict):
    """
    Game scores for home and away team, the a prefix is for away scores, h for home

    <ul id="330606118-aScores" class="score" style="display:block">
        <li id="330606118-alshT" class="finalScore">3</li>
        <li id="330606118-alshH">7</li>
        <li id="330606118-alshE">0</li>
    </ul>

    Scores are stored in  a 3-tuple (R,H,E)
    """

    away_score_list = mlbSoup.find('ul', id=gameID+"-aScores", class_="score")
    scores = away_score_list.contents
    if scores and len(scores)==3:
        dataDict['away_score'] = (unicode(scores[0].string),
                                  unicode(scores[1].string),
                                  unicode(scores[2].string))

    home_score_list = mlbSoup.find('ul', id=gameID+"-hScores", class_="score")
    scores = home_score_list.contents
    if scores and len(scores)==3:
        dataDict['home_score'] = (unicode(scores[0].string),
                                  unicode(scores[1].string),
                                  unicode(scores[2].string))

def pull_inning_scores(mlbSoup, gameID, dataDict):
    """
    Inning by inning scores for away and home team

    <td style="width: 17px;" id="330615101-als0">0</td>
    """

    scoreID = re.compile(gameID+'-hls[0-9][0-9]?')
    away_score_list = mlbSoup.find_all('td', id=scoreID)

    scoreID = re.compile(gameID+'-als[0-9][0-9]?')
    home_score_list = mlbSoup.find_all('td', id=scoreID)

    dataDict['away_inning_score'] = [tag.string for tag in away_score_list]
    dataDict['home_inning_score'] = [tag.string for tag in home_score_list]


def pull_current_pitching(mlbSoup, gameID, dataDict):
    """
    Team fielding
    <li id="330606118-currentPitcherHeader" style="display: block;">
        <strong>Pitching (Bal):</strong>
    </li>
    """
    fielding = mlbSoup.find('li', id=gameID+"-currentPitcherHeader")
    if fielding:
        dataDict['current_fielding'] = unicode(fielding.contents[0].string)


def pull_current_batting(mlbSoup, gameID, dataDict):
    """
    Team batting
    <li id="330606118-currentBatterHeader" style="display: block;">
        <strong>Batting (Hou):</strong>
    </li>
    """
    batting = mlbSoup.find('li', id=gameID+"-currentBatterHeader")
    if batting:
        dataDict['current_batting'] = unicode(batting.contents[0].string)


def pull_current_batter(mlbSoup, gameID, dataDict):
    """
    current player batting
    <li id="330606118-currentBatterName" style="display: block;">
        <a href="http://espn.go.com/mlb/player/_/id/4594/carlos-pena">C. Pena</a>
    </li>
    """
    currentBatter = mlbSoup.find('li', id=gameID+"-currentBatterName")
    if currentBatter:
        dataDict['current_batter'] = unicode(currentBatter.contents[0].string)


def pull_current_batter_stats(mlbSoup, gameID, dataDict):
    """
    current batter stats
    <li id="330606118-currentBatterStats" style="display: block; font-size: 0.9em;">0-2&nbsp;</li>
    """
    currentBatterStats = mlbSoup.find('li', id=gameID+"-currentBatterStats")
    if currentBatterStats:
        dataDict['current_batter_stats'] = unicode(currentBatterStats.string)


def pull_current_pitcher(mlbSoup, gameID, dataDict):
    """
    current player pitching
    <li id="330606118-currentPitcherName" style="display: block;">
        <a href="http://espn.go.com/mlb/player/_/id/29310/miguel-gonzalez">M. Gonzalez</a>
    </li>
    """
    currentPitcher = mlbSoup.find('li', id=gameID+"-currentPitcherName")
    if currentPitcher:
        dataDict['current_pitcher'] = unicode(currentPitcher.contents[0].string)


def pull_current_pitcher_stats(mlbSoup, gameID, dataDict):
    """
    current pitcher stats
    <li id="330606118-currentPitcherStats" style="display: block; font-size: 0.9em;">5.2 IP, 1 ER, 7 K</li>
    """
    currentPitcherStats = mlbSoup.find('li', id=gameID+"-currentPitcherStats")
    if currentPitcherStats:
        dataDict['current_pitcher_stats'] = unicode(currentPitcherStats.string)

def pull_ball_count(mlbSoup, gameID, dataDict):
    """
    current number of balls, there are three spaces for balls with links to images
    circle_off = no ball, circle_on = ball, need to count the number of circle_on images
    of the three displayed

    <img id="330616105-ball-1" src="http://a.espncdn.com/prod/assets/circle_off.png">
    """

    ballID = re.compile(gameID+'-ball-[1-3]')
    ball_imgs = mlbSoup.find_all('img', id=ballID)
    balls = ['circle_on' in tag['src'] for tag in ball_imgs]
    dataDict['num_balls'] = balls.count(True)

def pull_strike_count(mlbSoup, gameID, dataDict):
    """
    current number of strikes, HTML structure is essentially identical to pull_ball_count
    <img id="330616105-strike-1" src="http://a.espncdn.com/prod/assets/circle_on.png">
    """

    strikeID = re.compile(gameID+'-strike-[1-2]')
    strike_imgs = mlbSoup.find_all('img', id=strikeID)
    strikes = ['circle_on' in tag['src'] for tag in strike_imgs]
    dataDict['num_strikes'] = strikes.count(True)

def pull_out_count(mlbSoup, gameID, dataDict):
    """
    current number of outs, HTML structure is essentially identical to pull_ball_count
    and pull_strike_count

    <img id="330616130-out-1" src="http://a.espncdn.com/prod/assets/circle_off.png">
    """

    outID = re.compile(gameID+'-out-[1-2]')
    out_imgs = mlbSoup.find_all('img', id=outID)
    outs = ['circle_on' in tag['src'] for tag in out_imgs]
    dataDict['num_outs'] = outs.count(True)


def pull_last_play(mlbSoup, gameID, dataDict):
    """
    last play
    <span id="330606118-lastPlayText">Pitch 3: ball 3</span>
    """
    lastPlay = mlbSoup.find('span', id=gameID+"-lastPlayText")
    if lastPlay:
        dataDict['last_play'] = unicode(lastPlay.string)


def pull_homeruns(mlbSoup, gameID, dataDict):
    """
    home and away homeruns
    <span id="330606107-awayHomers">
        <strong>MIN:&nbsp;</strong>
        <a href="http://espn.go.com/mlb/player/_/id/6304/ryan-doumit">Doumit</a>
        &nbsp;(8)
    </span>
    """

    awayHomers = mlbSoup.find('span', id=gameID+"-awayHomers")
    if awayHomers and len(awayHomers.contents) > 0:
        homer_batters = map(lambda tag: unicode(tag.string),
                                awayHomers.contents[1::2])
        num_homers = map(lambda s: unicode(s).strip('()'),
                                awayHomers.contents[2::2])

        dataDict['away_homeruns'] = zip(homer_batters, num_homers)

    homeHomers = mlbSoup.find('span', id=gameID+"-homeHomers")
    if homeHomers and len(homeHomers.contents) > 0:
        homer_batters = map(lambda tag: unicode(tag.string),
                                awayHomers.contents[1::2])
        num_homers = map(lambda s: unicode(s).strip('()'),
                                awayHomers.contents[2::2])

        dataDict['home_homeruns'] = zip(homer_batters, num_homers)


def pull_winning_pitcher(mlbSoup, gameID, dataDict):
    """
    <span id="330607116-winningPitcher">
        <strong>W:&nbsp;</strong>
        <a href="http://espn.go.com/mlb/player/_/id/6211/francisco-liriano">Liriano</a>
        &nbsp;(4-2)&nbsp;&nbsp;
    </span>
    """
    winningPitcher = mlbSoup.find('span', id=gameID+"-winningPitcher")
    if winningPitcher and len(winningPitcher) == 3:
        dataDict['winning_pitcher'] = map(unicode,
                                                (winningPitcher.contents[1].string,
                                                winningPitcher.contents[2]))


def pull_losing_pitcher(mlbSoup, gameID, dataDict):
    """
    <span id="330607116-losingPitcher">
        <strong>L:&nbsp;</strong>
        <a href="http://espn.go.com/mlb/player/_/id/6211/francisco-liriano">Liriano</a>
        &nbsp;(4-2)&nbsp;&nbsp;
    </span>
    """
    losingPitcher = mlbSoup.find('span', id=gameID+"-losingPitcher")
    if losingPitcher and len(losingPitcher.contents) == 3:
        dataDict['losing_pitcher'] = map(unicode,
                                                (losingPitcher.contents[1].string,
                                                losingPitcher.contents[2]))


def pull_saving_pitcher(mlbSoup, gameID, dataDict):
    """
    <span id="330607116-losingPitcher">
        <strong>W:&nbsp;</strong>
        <a href="http://espn.go.com/mlb/player/_/id/6211/francisco-liriano">Liriano</a>
        &nbsp;(4-2)&nbsp;&nbsp;
    </span>
    """
    savingPitcher = mlbSoup.find('span', id=gameID+"-savingPitcher")
    if savingPitcher and len(savingPitcher.contents) == 3:
        dataDict['saving_pitcher'] = map(unicode,
                                                (savingPitcher.contents[1].string,
                                                savingPitcher.contents[2]))

def pull_event_data(mlbSoup, events, gameID, dataDict):
    """
        insert doc string
    """
    gameSoup = mlbSoup.find('div', id=gameID+"-gamebox")
    events = dict(events[0].items() + events[1].items())
    gameState = events[gameID]

    if gameState == 'preview' or gameState == 'final' or gameState == 'in_game':
        pull_team_names(gameSoup, gameID, dataDict)
        pull_team_records(gameSoup, gameID, dataDict)
        pull_team_starters(gameSoup, gameID, dataDict)
        pull_game_status(gameSoup, gameID, dataDict )
        pull_game_note(gameSoup, gameID, dataDict)

    if gameState == 'in_game':
        pull_game_scores(gameSoup, gameID, dataDict)
        pull_current_pitching(gameSoup, gameID, dataDict)
        pull_current_batting(gameSoup, gameID, dataDict)
        pull_current_batter(gameSoup, gameID, dataDict)
        pull_current_pitcher(gameSoup, gameID, dataDict)
        pull_current_pitcher_stats(gameSoup, gameID, dataDict)
        pull_current_batter_stats(gameSoup, gameID, dataDict)
        pull_strike_count(gameSoup, gameID, dataDict)
        pull_ball_count(gameSoup, gameID, dataDict)
        pull_out_count(gameSoup, gameID, dataDict)
        pull_last_play(gameSoup, gameID, dataDict)
        pull_homeruns(gameSoup, gameID, dataDict)
        pull_inning_scores(gameSoup, gameID, dataDict)


    if gameState == 'final' and 'Final' in dataDict['game_status']:
        pull_winning_pitcher(gameSoup, gameID, dataDict)
        pull_losing_pitcher(gameSoup, gameID, dataDict)
        pull_saving_pitcher(gameSoup, gameID, dataDict)
        pull_inning_scores(gameSoup, gameID, dataDict)

def format_event_data(dataDict):
    """
    function to format data contained in a data dict
    since the scraped score data could change at any time it is useful to make
    this optional
    """
    def format_record(rec):
        return rec.strip('()').replace(',','').split()[:-1]

#ESPN MLB Scoreboard URL
ESPN_MLB = "http://scores.espn.go.com/mlb/scoreboard"

#User Agent - Identifying self as Mozilla, default for urllib is "Python-urllib/x.y"
header = {'User-Agent':
          "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0)"}
#Open url
mlbReq = urllib2.Request(ESPN_MLB, None, header)

try:
    mlbRes = urllib2.urlopen(mlbReq)
except URLError as e:
    print(e.reason)

#Make SoupStrainer to selectively parse the MLB score data from the page


strainer = SoupStrainer('div', id=re.compile(r"games"))

mlbSoup = BeautifulSoup(urllib2.urlopen(ESPN_MLB), ["lxml", "xml"], parse_only=strainer)

AL, NL = pull_game_ids(mlbSoup)
events = dict(AL.items() + NL.items())
#final_game = '330607102'
#in_game = '330615101'

#preview_game = '330607112'
#330615101
#data_final = {}
#data_in_game = {}
#data_preview = {}
#
#pull_event_data(mlbSoup, events, final_game, data_final)
#pull_event_data(mlbSoup, events, in_game, data_in_game)
#pull_event_data(mlbSoup, events, preview_game, data_preview)

pprint.pprint(events)
print
data={}
for game in events:
    pull_event_data(mlbSoup, [AL, NL], game, data)
    print '-----------------'+game+'---------------------------'
    pprint.pprint(data)
    print '\n'
    data={}

#pprint.pprint(data_final)
#print
#pprint.pprint(data_in_game)
#print
#pprint.pprint(data_preview)

#<div id="330606102-homeRuns" class="border-top game-info-module" style="display: block;"><strong>HR&nbsp;&nbsp;&nbsp;</strong><span id="330606102-awayHomers"><strong>TEX:&nbsp;</strong><a href="http://espn.go.com/mlb/player/_/id/3878/adrian-beltre">Beltre</a>&nbsp;(13), <a href="http://espn.go.com/mlb/player/_/id/5371/jeff-baker">Baker</a>&nbsp;(7)</span><span id="330606102-homeHomers"></span></div>
#homers = mlbSoup.find('span', id="330606102-awayHomers")
#print homers.contents
#print unicode(homers.string)
#print homers.prettify(encoding='utf-8')
#pull_game_info(mlbSoup, '330606107', test_data)
#pull_game_scores(mlbSoup, '330606107', test_data)
#pull_game_details(mlbSoup, '330606107', test_data)

#al, nl = pull_game_ids(mlbSoup)
#
#
#print "AL league games: ", al
#print "NL league games: ", nl
#print test_data

#print timeit.timeit(BeautifulSoup(urllib2.urlopen(ESPN_MLB),"html.parser", parse_only=make_strainer()),
#        number=1)

#print diagnose(urllib2.urlopen(ESPN_MLB))
