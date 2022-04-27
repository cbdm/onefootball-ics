'''onefootball2ics.py
Author: Caio (caio@cbmelo.com)
Description: This script creates an ics calendar with a team's fixtures that are parsed from onefootball.
'''

from requests import get
from dateutil.parser import parse
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from ics import Calendar, Event
from pickle import loads, dumps

class Match(object):
    '''Object to store the information for a single match from the fixtures list.'''
    def __init__(self, team1, team2, datetime, tournament):
        self.team1 = team1
        self.team2 = team2
        self.datetime = datetime
        self.tournament = tournament


    def create_event(self, event_length):
        '''Convert the match info into a calendar event.'''
        e = Event()
        e.name = f'[{self.tournament}] {self.team1} - {self.team2}'
        e.begin = self.datetime
        e.duration = event_length
        return e


    def __str__(self):
        return f'[{self.tournament}] {self.team1} - {self.team2} @ {self.datetime}'


def get_page(is_team, of_id):
    '''Request the fixtures page from onefootball for the desired team/competition.'''
    if is_team:
        url = f'https://onefootball.com/en/team/{of_id}/fixtures'
    else:
        url = f'https://onefootball.com/en/competition/{of_id}/fixtures'
    resp = get(url)
    if resp.status_code != 200:
        raise Exception(f"Could not sucessfully fetch '{url}'")
    return resp.text


def get_matches(is_team, soup):
    '''Find and parse all match cards in the page.'''

    def _get_match_datetime(simple_match_card):
        '''Parse the date and time from the match card.'''
        content = simple_match_card.find('div', {'class': 'simple-match-card__match-content'})
        time = content.find('time').get('datetime')
        return parse(time)

    def _get_match_teams(simple_match_card):
        '''Parse the team names and possible score from the match card.'''
        # Find the team info cards.
        content = simple_match_card.find('div', {'class': 'simple-match-card__teams-content'})
        teams = content.find_all('div', {'class': 'simple-match-card-team'})
        assert len(teams) == 2
        
        # Parse both teams individually and add the score to the team's name if the match has happened.
        team1 = teams[0].find('span', {'class': 'simple-match-card-team__name'}).text.strip()
        score1 = teams[0].find('span', {'class': 'simple-match-card-team__score'}).text.strip()
        if score1:
            team1 = f'{team1} ({score1})'

        team2 = teams[1].find('span', {'class': 'simple-match-card-team__name'}).text.strip()
        score2 = teams[1].find('span', {'class': 'simple-match-card-team__score'}).text.strip()
        if score2:
            team2 = f'({score2}) {team2}'

        return team1, team2

    def _get_match_tournament(simple_match_card):
        '''Parse the tournament from the match card.'''
        content = simple_match_card.find('footer')
        return content.find('p').text.strip()

    # Check if it's a competition calendar, if it is, let's find out the name.
    if not is_team:
        tournament = soup.find('p', {'class': 'title-2-bold'}).text.strip()
    
    # Finds all the match cards in the website.
    matches = soup.find_all('li', {'class': 'simple-match-cards-list__match-card'})
    # Process each match card individually and create a list of new matches.
    new_matches = []
    for match in matches:
        match_time = _get_match_datetime(match)
        team1, team2 = _get_match_teams(match)
        # Search for the competition only if this is a team calendar.
        if is_team: tournament = _get_match_tournament(match)
        new_matches.append(Match(team1, team2, match_time, tournament))
    return new_matches


def create_calendar(matches, event_length):
    '''Create a new ics calendar with the parsed matches.'''
    # Create an empty calendar and add one event for each match.
    cal = Calendar()
    for match in matches:
        cal.events.add(match.create_event(event_length))
    return cal


def main(is_team, of_id, event_length, *, redis_db={}, freshness=timedelta(days=1.5)):
    '''Parse the fixtures page from onefootball into an ics calendar.'''
    cur_date = datetime.now(timezone.utc)
    lookup_key = f'{"team" if is_team else "comp"}/{of_id}'
    
    # Get the cached data (if any).
    data = redis_db.get(lookup_key)
    if data: data = loads(data)
    
    # Check if the data exists and is still fresh.
    if data and data['last_updated'] + freshness >= cur_date:
        matches = data['matches']
    
    # Data doesn't exist or isn't fresh, so we'll update it.
    else:
        # Get the page and parse it into beautifulsoup.
        html = get_page(is_team, of_id)
        soup = BeautifulSoup(html, 'lxml')
        # Get the new info for the matches.
        matches = get_matches(is_team, soup)
        # Update our cache.
        redis_db[lookup_key] = dumps({'matches': matches, 'last_updated': cur_date})
    
    # Create and return a calendar with the matches.
    return create_calendar(matches, event_length)


if __name__ == '__main__':
    # Example values for my use-case :)
    is_team = True
    of_id = 'atletico-mineiro-1683'
    event_length = timedelta(hours=2)
    print('Galo\'s Calendar:')
    print(main(is_team, of_id, event_length))
    
    print()
    print()
    
    is_team = False
    of_id = 'conmebol-libertadores-76'
    event_length = timedelta(hours=2, minutes=30)
    print('Libertadores\' Calendar:')
    print(main(is_team, of_id, event_length))
