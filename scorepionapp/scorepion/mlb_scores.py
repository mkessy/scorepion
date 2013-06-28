import re
import urllib2, urllib
import parse_html_scores as parsemlb
from bs4 import BeautifulSoup, SoupStrainer
import simplejson as json

#URLS required for scraping
ESPN_MLB = "http://scores.espn.go.com/mlb/scoreboard"

#User Agent - Identifying self as Mozilla, default for urllib is "Python-urllib/x.y"
header = {'User-Agent':
          "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0)"}

mlb_request = urllib2.Request(ESPN_MLB, None, header)

try:
    mlb_html = urllib2.urlopen(mlb_request)
except urllib2.URLError as e:
    raise

mlb_strainer = SoupStrainer('div', id=re.compile(r"games"))
MLB_SOUP = BeautifulSoup(mlb_html, ["lxml", "xml"], parse_only=mlb_strainer)

raw_events = parsemlb.pull_game_ids(MLB_SOUP)

def return_json(function):
    """Decorator to return json output"""

    def jsonify(*args, **kwargs):
        return json.dumps(function(*args, **kwargs), sort_keys=True, indent=4*' ')

    return jsonify

def get_events():
    """Returns all events
    events have three "label":"value" pairs
    game_id - ########
    """

    event_list = {}

    for game_id, game_state in raw_events.items():
        home, away = parsemlb.pull_team_names(MLB_SOUP, game_id)
        event_list[game_id] = {'state':game_state, 'teams':{'home':home,
                                                            'away':away}}
    return event_list

@return_json
def get_all_events():
    """No docstring yet"""
    return get_events()

@return_json
def get_preview_events():
    """No docstring yet"""

    events = get_events()
    preview_events = dict((k,v) for k, v in events.items() if v['state']=='preview')

    return preview_events

@return_json
def get_in_game_events():
    """Not yet implemented"""

    events = get_events()
    in_game_events = dict((k,v) for k, v in events.items() if v['state']=='in_game')

    return in_game_events

@return_json
def get_final_events():
    """Not yet implemented"""

    events = get_events()
    final_events = dict((k,v) for k, v in events.items() if v['state']=='in_game')

    return final_events

@return_json
def get_game_score(game_id):
    """Returns the home and away team, the game status,
    and the score"""

    game_score = {}
    home, away = parsemlb.pull_team_names(MLB_SOUP, game_id)
    hrec, arec = parsemlb.pull_team_records(MLB_SOUP, game_id)
    game_status = parsemlb.pull_game_status(MLB_SOUP, game_id)
    awayscore, homescore = parsemlb.pull_game_scores(MLB_SOUP, game_id)

    home_overall_rec, home_away_rec = hrec.strip('()').replace(',', '').split()[:-1]
    away_overall_rec, away_away_rec = arec.strip('()').replace(',', '').split()[:-1]

    home_record = {'overall_record':home_overall_rec,
                   'away_record':home_away_rec}

    away_record = {'overall_record':away_overall_rec,
                   'away_record':away_away_rec}

    ascore = {}
    hscore = {}

    ascore['runs'], ascore['hits'], ascore['errors'] = awayscore
    hscore['runs'], hscore['hits'], hscore['errors'] = homescore

    game_score['home'], game_score['away'] = home, away
    game_score['away_score'] = ascore
    game_score['home_score'] = hscore
    game_score['home_record'] = home_record
    game_score['away_record'] = away_record

    #for preview games the status is a time, i.e. 9:00PM ET, it may be a good
    #idea to convert this to a more standard time measurement at some point
    game_score['status'] = game_status
    game_score['state'] = raw_events[game_id]

    return game_score


def get_in_game_details(game_id):
    """Details for games that are 'in_game'"""

    in_game_details = {}
    reabr = re.compile(r'\((?P<abr>[a-zA-Z]{3})\)')
    pitching = parsemlb.pull_current_pitching(MLB_SOUP, game_id)
    batting = parsemlb.pull_current_batting(MLB_SOUP, game_id)
    in_game_details['fielding_team'] = reabr.search(pitching).group('abr')
    in_game_details['batting_team'] = reabr.search(batting).group('abr')

    in_game_details['current_batter'] = {'player':parsemlb.pull_current_batter(MLB_SOUP, game_id),
                            'game_record':parsemlb.pull_current_batter_stats(MLB_SOUP, game_id)}

    rePitcher = re.compile(r'(?P<IP>[0-9][0-9]*.[0-9]+) IP, (?P<ER>[0-9]+) ER, (?P<K>[0-9]*[0-9]+) K')
    stats = rePitcher.search(parsemlb.pull_current_pitcher_stats(MLB_SOUP, game_id))

    in_game_details['current_pitcher'] = {'player':parsemlb.pull_current_pitcher(MLB_SOUP, game_id),
                                          'IP':stats.group('IP'),
                                          'ER':stats.group('ER'),
                                          'K':stats.group('K')}

    in_game_details['num_strikes'] = parsemlb.pull_strike_count(MLB_SOUP, game_id)
    in_game_details['num_balls'] = parsemlb.pull_ball_count(MLB_SOUP, game_id)
    in_game_details['num_outs'] = parsemlb.pull_out_count(MLB_SOUP, game_id)
    in_game_details['last_play'] = parsemlb.pull_last_play(MLB_SOUP, game_id)

    return in_game_details



@return_json
def get_game_details(game_id):
    """Returns all available game details. Details available depends on the game state.
    UPDATE DOC TO INCLUDE DETAILS AVAILABLE FOR EACH GAME STATE"""

    #all games regardless of state will contain the details returned by the
    #get_game_details method

    #need to encode from JSON first
    game_details = json.loads(get_game_score(game_id))

    game_state = game_details['state']

    #starting pitchers
    home_starter, away_starter = parsemlb.pull_team_starters(MLB_SOUP, game_id)
    rePitcher = re.compile(r'(?P<rec>[0-9]+-[0-9]+), (?P<ERA>[0-9]*.[0-9][0-9])')
    stats = rePitcher.search(home_starter[1])
    print home_starter[0]
    print home_starter[1]
    game_details['home_starter'] = {'player':home_starter[0],
                                    'record':stats.group('rec'),
                                    'ERA':stats.group('ERA')}

    stats = rePitcher.search(away_starter[1])
    game_details['away_starter'] = {'player':away_starter[0],
                                    'record':stats.group('rec'),
                                    'ERA':stats.group('ERA')}

    game_details['game_note'] =  parsemlb.pull_game_note(MLB_SOUP,game_id)

    if game_state == 'in_game':
        game_details = dict(game_details.items() + get_in_game_details(game_id).items())

    return game_details



#def pull_event_data(mlbSoup,  gameID):
#    """
#        insert doc string
#    """
#    gameSoup = mlbSoup.find('div', id=gameID+"-gamebox")
#    gameState = events[gameID]
#
#    if gameState == 'preview' or gameState == 'final' or gameState == 'in_game':
#        pull_team_names(gameSoup, gameID, dataDict)
#        pull_team_records(gameSoup, gameID, dataDict)
#        pull_team_starters(gameSoup, gameID, dataDict)
#        pull_game_status(gameSoup, gameID, dataDict )
#        pull_game_note(gameSoup, gameID, dataDict)
#
#    if gameState == 'in_game':
#        pull_game_scores(gameSoup, gameID, dataDict)
#        pull_current_pitching(gameSoup, gameID, dataDict)
#        pull_current_batting(gameSoup, gameID, dataDict)
#        pull_current_batter(gameSoup, gameID, dataDict)
#        pull_current_pitcher(gameSoup, gameID, dataDict)
#        pull_current_pitcher_stats(gameSoup, gameID, dataDict)
#        pull_current_batter_stats(gameSoup, gameID, dataDict)
#        pull_strike_count(gameSoup, gameID, dataDict)
#        pull_ball_count(gameSoup, gameID, dataDict)
#        pull_out_count(gameSoup, gameID, dataDict)
#        pull_last_play(gameSoup, gameID, dataDict)
#        pull_homeruns(gameSoup, gameID, dataDict)
#        pull_inning_scores(gameSoup, gameID, dataDict)
#
#
#    if gameState == 'final' and 'Final' in dataDict['game_status']:
#        pull_winning_pitcher(gameSoup, gameID, dataDict)
#        pull_losing_pitcher(gameSoup, gameID, dataDict)
#        pull_saving_pitcher(gameSoup, gameID, dataDict)
#        pull_inning_scores(gameSoup, gameID, dataDict)




def main():
    event_list = get_events()

    for game_id in event_list.keys():
        print game_id
        print
        print get_game_details(game_id)




    #print(get_all_events())
    #print(get_preview_events())
    #print(get_in_game_events())
    #print(get_final_events())


if __name__ == '__main__':
    main()


