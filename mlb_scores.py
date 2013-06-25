
import urllib2, urllib
import parse_html_scores
from bs4 import BeautifulSoup, SoupStrainer
import simplejson as json

#URLS required for scraping
ESPN_MLB = "http://scores.espn.go.com/mlb/scoreboard"

#User Agent - Identifying self as Mozilla, default for urllib is "Python-urllib/x.y"
header = {'User-Agent':
          "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0)"}

mlb_request = urllib2.Request(ESPN_MLB, None, header)

try:
    mlb_html = urlib2.urlopen(mlb_request)
except URLError as e:
    raise

mlb_strainer = SoupStrainer('div', id=re.compile(r"games"))
MLB_SOUP = BeautifuSoup(mlb_html, ["lxml", "xml"], parse_only=mlb_strainer)

data = {}
events = pull_game_ids(MLB_SOUP)

def get_events():
    """Returns an event JSON object
    events have three "label":"value" pairs
    game_id - ########
    """

    #immplementation

    return json.dumps(events)

def get_preview_events():
    """Not yet implemented"""

def get_in_game_events():
    """Not yet implemented"""

def get_final_events():
    """Not yet implemented"""






