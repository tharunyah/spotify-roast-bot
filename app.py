from flask import Flask, request, redirect, render_template_string
import requests
import os
import urllib.parse
import random

app = Flask(__name__)

# Homepage template
HOME_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Spotify Roaster</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 2rem; }
        a { 
            display: inline-block;
            margin-top: 1rem;
            padding: 0.5rem 1rem;
            background-color: #1DB954;
            color: white;
            text-decoration: none;
            border-radius: 4px;
        }
        a:hover { background-color: #1ed760; }
    </style>
</head>
<body>
    <h1>Spotify Roaster 🔥</h1>
    <p>Get your music taste absolutely destroyed!</p>
    <a href="/auth/spotify">Login with Spotify</a>
</body>
</html>
"""

# Roast result template
ROAST_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Your Musical Crimes</title>
    <style>
        body { 
            font-family: 'Courier New', monospace; 
            background: #000;
            color: #FF2D70;
            text-align: center;
            padding: 20px;
        }
        .roast-box {
            border: 3px solid #FF2D70;
            padding: 20px;
            max-width: 600px;
            margin: 20px auto;
            text-shadow: 0 0 5px rgba(255,45,112,0.5);
        }
        .therapy-bill {
            color: #00F0FF;
            border-top: 2px dashed #FF2D70;
            margin-top: 15px;
            padding-top: 10px;
        }
        .track-list {
            color: #FFFF00;
            font-size: 12px;
            margin-top: 20px;
            border-top: 1px solid #FF2D70;
            padding-top: 10px;
        }
        a {
            color: #00F0FF;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="roast-box">
        <h2>☠️ YOUR MUSIC TASTE IS A CRIME ☠️</h2>
        <p>{{ roast|safe }}</p>
        <div class="therapy-bill">
            <h3>YOUR THERAPY BILL:</h3>
            <p>{{ therapy_bill|safe }}</p>
        </div>
        <div class="track-list">
            <h4>EVIDENCE OF YOUR CRIMES:</h4>
            {% for track in tracks %}
            <div>🎵 {{ track.name }} - {{ track.artists[0].name }}</div>
            {% endfor %}
        </div>
        <br>
        <a href="/">← Roast Someone Else</a>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HOME_TEMPLATE)

@app.route('/auth/spotify')
def spotify_auth():
    scope = 'user-top-read user-read-recently-played'
    params = {
        'client_id': os.environ.get('CLIENT_ID'),
        'response_type': 'code',
        'redirect_uri': os.environ.get('REDIRECT_URI'),
        'scope': scope,
        'show_dialog': 'true'
    }
    
    auth_url = f"https://accounts.spotify.com/authorize?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

@app.route('/auth/spotify/callback')
@app.route('/callback')
def spotify_callback():
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        return f"Authorization failed: {error}", 400
    
    if not code:
        return "Authorization code not provided", 400
    
    try:
        # Check environment variables first
        client_id = os.environ.get('CLIENT_ID')
        client_secret = os.environ.get('CLIENT_SECRET')
        redirect_uri = os.environ.get('REDIRECT_URI')
        groq_key = os.environ.get('GROQ_API_KEY')
        
        if not all([client_id, client_secret, redirect_uri, groq_key]):
            return f"""
            <h2>Missing Environment Variables!</h2>
            <p>CLIENT_ID: {'✅' if client_id else '❌'}</p>
            <p>CLIENT_SECRET: {'✅' if client_secret else '❌'}</p>
            <p>REDIRECT_URI: {'✅' if redirect_uri else '❌'}</p>
            <p>GROQ_API_KEY: {'✅' if groq_key else '❌'}</p>
            <a href="/">← Go Back</a>
            """
        
        # Exchange code for access token
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'client_secret': client_secret
        }
        
        print("Requesting Spotify token...")
        token_response = requests.post(
            'https://accounts.spotify.com/api/token',
            data=token_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        print(f"Token response status: {token_response.status_code}")
        print(f"Token response text: {token_response.text}")
        
        if token_response.status_code != 200:
            return f"Spotify token error: {token_response.text}", 400
        
        token_json = token_response.json()
        access_token = token_json['access_token']
        
        # Rest of your code...
        
    except Exception as e:
        print(f"DETAILED ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500
        
        # Get user's music data
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Get top tracks
        top_tracks_response = requests.get(
            'https://api.spotify.com/v1/me/top/tracks?limit=10',
            headers=headers
        )
        top_tracks = top_tracks_response.json()['items']
        
        # Get top artists
        try:
            top_artists_response = requests.get(
                'https://api.spotify.com/v1/me/top/artists?limit=5',
                headers=headers
            )
            top_artists = top_artists_response.json().get('items', [])
        except:
            top_artists = []
        
        # Get recent tracks
        try:
            recent_response = requests.get(
                'https://api.spotify.com/v1/me/player/recently-played?limit=5',
                headers=headers
            )
            recent_tracks = [item['track'] for item in recent_response.json().get('items', [])]
        except:
            recent_tracks = []
        
        # Generate roast using Groq
        roast_prompt = f"""
        ROAST THIS PERSON'S MUSIC TASTE LIKE THEY JUST MADE YOU LISTEN TO IT ON A 12-HOUR ROAD TRIP.
        
        Top Tracks: {', '.join([f"{track['name']} by {track['artists'][0]['name']}" for track in top_tracks])}
        
        Top Artists: {', '.join([artist['name'] for artist in top_artists])}
        
        Recent Tracks: {', '.join([f"{track['name']} by {track['artists'][0]['name']}" for track in recent_tracks])}

        Rules:
        - Compare them to embarrassing figures (e.g. "You're the musical equivalent of a minion meme")
        - Roast their artist choices and song preferences
        - Diagnose fake mental conditions ("chronic vibe deficiency")
        - Maximum savagery, minimum mercy
        - Focus on genre mixing, repetitive artists, or questionable taste patterns
        - Keep it under 200 words
        """
        
        groq_response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            json={
                'model': 'llama3-8b-8192',
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are Simon Cowell if he snorted wasabi. Roast music taste with cruel comparisons, fake diagnoses, and maximum savagery. Avoid racism, sexism, real personal attacks.'
                    },
                    {
                        'role': 'user',
                        'content': roast_prompt
                    }
                ],
                'temperature': 0.95,
                'max_tokens': 250
            },
            headers={'Authorization': f'Bearer {os.environ.get("GROQ_API_KEY")}'}
        )
        
        roast = groq_response.json()['choices'][0]['message']['content']
        
        # Generate therapy bill
        therapy_bill = generate_therapy_bill(top_tracks)
        
        return render_template_string(
            ROAST_TEMPLATE,
            roast=roast.replace('\n', '<br>'),
            therapy_bill=therapy_bill,
            tracks=top_tracks[:5]
        )
        
    except Exception as e:
        print(f"Error: {e}")
        return f"""
        <html>
        <body style="font-family: Arial; text-align: center; padding: 2rem;">
            <h2>💀 Something went wrong! 💀</h2>
            <p>Even I can't roast what I can't see. Try again!</p>
            <div style="background: #f0f0f0; padding: 10px; margin: 20px; font-size: 12px;">
                <strong>Error:</strong> {str(e)}
            </div>
            <a href="/" style="color: #1DB954;">← Go Back</a>
        </body>
        </html>
        """, 500

def generate_therapy_bill(tracks):
    conditions = [
        "Chronic Basicness",
        "Terrible Taste Disorder", 
        "Guilty Pleasure Addiction",
        "Main Character Syndrome",
        "Playlist Personality Disorder",
        "Genre Confusion Syndrome"
    ]
    
    treatments = [
        "Hipster Conversion Therapy",
        "Taste Transfusion",
        "Shame Reduction Counseling",
        "TikTok Detox Program",
        "Music Theory Bootcamp",
        "Indie Rock Rehabilitation"
    ]
    
    condition = random.choice(conditions)
    treatment = random.choice(treatments)
    cost = random.randint(500, 2500)
    sessions = random.randint(5, 15)
    
    return f"""
    • Diagnosis: {condition}<br>
    • Treatment: {treatment}<br>
    • Sessions Required: {sessions}<br>
    • Total Due: ${cost}.00<br>
    <small>Payable in eternal shame and better playlists</small>
    """

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))