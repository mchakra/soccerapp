from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
import requests
from datetime import datetime
from collections import defaultdict

API_FOOTBALL_KEY = "0721fe1e6cb9e84e75774ea3c2f10d3b"

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a random secret key

def user_exists(username):
    with open('users.txt', 'r') as file:
        users = file.readlines()
        for user in users:
            uname, _ = user.strip().split(',')
            if uname == username:
                return True
    return False

def register_user(username, password):
    with open('users.txt', 'a') as file:
        hashed_password = generate_password_hash(password)
        file.write(f"{username},{hashed_password}\n")

''''
def fetch_recent_matches():
    url = 'http://api.football-data.org/v4/competitions/PL/matches?status=FINISHED'
    headers = {'X-Auth-Token': '67865b93b6774cd9a1ef1b9b6c2d1ee9'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        matches = response.json().get('matches', [])[:5]  # Get only the last 5 matches
        news_items = []
        for match in matches:
            print(match)
            news_items.append(match)
        return news_items
    else:
        print("Failed to fetch matches:", response.status_code)
        return []
'''

def get_api_football_matches():
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://v3.football.api-sports.io/fixtures?date={today}"

    headers = {
        "x-apisports-key": API_FOOTBALL_KEY
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("API error:", response.status_code)
        return None

    fixtures = response.json().get("response", [])
    grouped_matches = defaultdict(list)

    for match in fixtures:
        league = match["league"]["name"]
        home = match["teams"]["home"]["name"]
        away = match["teams"]["away"]["name"]
        home_logo = match["teams"]["home"]["logo"]
        away_logo = match["teams"]["away"]["logo"]
        status = match["fixture"]["status"]["short"]
        score_home = match["goals"]["home"]
        score_away = match["goals"]["away"]
        score = f"{score_home}-{score_away}" if score_home is not None else "vs"
        time = match["fixture"]["date"][11:16]

        grouped_matches[league].append({
            "home": home,
            "away": away,
            "home_logo": home_logo,
            "away_logo": away_logo,
            "score": score,
            "status": status,
            "time": time
        })

    return dict(grouped_matches)

def get_api_football_scores():
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://v3.football.api-sports.io/fixtures?date={today}"
    headers = { "x-apisports-key": API_FOOTBALL_KEY }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None

    fixtures = response.json().get("response", [])
    grouped_scores = defaultdict(list)

    for match in fixtures:
        status = match["fixture"]["status"]["short"]
        if status not in ["FT", "AET", "PEN"]:
            continue  # Only final scores

        league = match["league"]["name"]
        home = match["teams"]["home"]["name"]
        away = match["teams"]["away"]["name"]
        home_logo = match["teams"]["home"]["logo"]
        away_logo = match["teams"]["away"]["logo"]
        score = f"{match['goals']['home']}-{match['goals']['away']}"
        time = match["fixture"]["date"][11:16]

        grouped_scores[league].append({
            "home": home,
            "away": away,
            "home_logo": home_logo,
            "away_logo": away_logo,
            "score": score,
            "status": status,
            "time": time
        })

    return dict(grouped_scores)

teams_by_league = {
    "Premier League": {
        "arsenal": {
            "name": "Arsenal FC",
            "full_name": "Arsenal Football Club",
            "founded": 1886,
            "stadium": "Emirates Stadium",
            "capacity": "60,704",
            "manager": "Mikel Arteta",
            "league": "Premier League",
            "logo": "https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg",
            "description": "Arsenal is a professional football club based in Islington, London. It plays in the Premier League and has a long history of success, both domestically and internationally.",
            "wiki": "https://en.wikipedia.org/wiki/Arsenal_F.C."
        }
    },
    "La Liga": {
        "realmadrid": {
            "name": "Real Madrid",
            "full_name": "Real Madrid Club de Fútbol",
            "founded": 1902,
            "stadium": "Santiago Bernabéu Stadium",
            "capacity": "81,044",
            "manager": "Carlo Ancelotti",
            "league": "La Liga",
            "logo": "https://upload.wikimedia.org/wikipedia/en/5/56/Real_Madrid_CF.svg",
            "description": "Real Madrid is a Spanish professional football club based in Madrid. It is widely recognized as one of the most successful clubs in football history.",
            "wiki": "https://en.wikipedia.org/wiki/Real_Madrid_CF"
        },
        "barcelona": {
            "name": "FC Barcelona",
            "full_name": "Futbol Club Barcelona",
            "founded": 1899,
            "stadium": "Spotify Camp Nou",
            "capacity": "99,354",
            "manager": "Xavi Hernández",
            "league": "La Liga",
            "logo": "https://upload.wikimedia.org/wikipedia/en/4/47/FC_Barcelona_%28crest%29.svg",
            "description": "Barcelona is a professional football club based in Barcelona, Catalonia, Spain. It is known for its iconic style of play and rivalry with Real Madrid.",
            "wiki": "https://en.wikipedia.org/wiki/FC_Barcelona"
        }
    }
}


def get_top_scorers(league_id=39, season=2023):
    url = f"https://v3.football.api-sports.io/players/topscorers?league={league_id}&season={season}"
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    try:
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return None

        scorers = []
        for item in response.json().get("response", []):
            player = item["player"]
            statistics = item["statistics"][0]
            scorers.append({
                "name": player["name"],
                "team": statistics["team"]["name"],
                "photo": player["photo"],
                "goals": statistics["goals"]["total"],
                "nationality": player["nationality"]
            })
        return scorers
    except Exception as e:
        print("API Error:", e)
        return None

def get_standings(league_id=39, season=2023):
    url = f"https://v3.football.api-sports.io/standings?league={league_id}&season={season}"
    
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        print(data)

        if data.get("response") and len(data["response"]) > 0:
            return data["response"][0]["league"]["standings"][0]
        else:
            return None
    except Exception as e:
        print("API Error:", e)
        return None

@app.route('/')
def home():
    # Load all 3 sources (you already have these elsewhere)
    all_news = [
        {
            "title": "Real Madrid are elimated from the UEFA Champions League",
            "image": "https://images2.minutemediacdn.com/image/upload/c_crop,w_4000,h_2666,x_0,y_0/c_fill,w_620,ar_3:2,f_auto,q_auto,g_auto/images/voltaxMediaLibrary/mmsport/real_madrid_cf_on_si/01js06tyt7wdn7chdyae.jpg",
            "summary": "Real Madrid were coming off of a season where they steamrolled to a La Liga title and also won the Champions League in the same season.",
            "id": 8
        },
        {
            "title": "Champions League: AC Milan drama",
            "image": "https://a57.foxsports.com/statics.foxsports.com/www.foxsports.com/content/uploads/2025/02/647/364/bellingham-goal.jpg?ve=1&tl=1",
            "summary": "The seven-time European champions were forced to settle for a 1-1 tie with Feyenoord.",
            "id": 2
        },
         {
            "title": "With the USMNT idle this February, coach Mauricio Pochettino and his staff hit the road",
            "image": "https://a57.foxsports.com/statics.foxsports.com/www.foxsports.com/content/uploads/2025/02/647/364/poch1.jpg?ve=1&tl=1",
            "summary": "After a whirlwind first few months in charge for coach Mauricio Pochetttino — the former Chelsea, PSG and Tottenham Hotspur manager was hired in September",
            "id": 3
        }
    ]
    # fetch matches
    match_groups = get_api_football_matches()

    # sample teams
    sample_teams = dict(list(teams_by_league["Premier League"].items())[:2])

    return render_template('index.html', 
                           news=all_news, 
                           matches=match_groups, 
                           teams=sample_teams)


@app.route('/matches')
def matches():
    match_groups = get_api_football_matches()
    return render_template('matches.html', match_groups=match_groups)

@app.route('/teams')
def teams():
    return render_template('teams.html', leagues=teams_by_league)

@app.route('/team/<team_id>')
def team_profile(team_id):
    # If you're using teams_data or teams_by_league
    # Combine all teams into one lookup dictionary
    all_teams = {}

    for league_teams in teams_by_league.values():
        all_teams.update(league_teams)

    team = all_teams.get(team_id)

    if not team:
        return "Team not found", 404

    return render_template('team_profile.html', team=team)

@app.route('/scores')
def scores():
    score_groups = get_api_football_scores()
    return render_template('scores.html', match_groups=score_groups)

@app.route('/news')
def news():
    return render_template('news.html')

@app.route('/topscorers')
def topscorers():
    scorers = get_top_scorers()
    return render_template('topscorers.html', scorers=scorers)

@app.route('/standings')
def standings():
    table = get_standings()
    return render_template('standings.html', table=table)

@app.route('/article/<int:id>')
def article(id):
    return render_template(f'article{id}.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not user_exists(username):
            register_user(username, password)
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('signin'))
        else:
            flash('Username already exists. Choose a different one.', 'error')
    return render_template('register.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if check_user(username, password):
            session['username'] = username
            session['signed_in'] = True
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password. Please try again.', 'error')
    return render_template('login.html')

def check_user(username, password):
    with open('users.txt', 'r') as file:
        users = file.readlines()
        for user in users:
            uname, pwd = user.strip().split(',')
            if uname == username and check_password_hash(pwd, password):
                return True
    return False

@app.route('/signout')
def signout():
    session.pop('username', None)
    session.pop('signed_in', None)
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
