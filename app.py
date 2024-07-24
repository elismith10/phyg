from flask import Flask, render_template, request
import pandas as pd
from supabase import create_client, Client

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    genre = request.form.get('genre')
    if genre:
        url = "https://uwipiyaoidfgmbjbsjuq.supabase.co"
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV3aXBpeWFvaWRmZ21iamJzanVxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjE0MDQ4NzksImV4cCI6MjAzNjk4MDg3OX0.UEfvSlN-FdAdwonkYEiaz5dLGwY7TSFQNkvR_08AHDk"
        client = create_client(url, key)

        response = client.table("songs").select("*").eq("genre", genre.lower()).execute()
        data = response.data

        df = pd.DataFrame(data)

        selected_song = df.sample(n=1).iloc[0]

        print(selected_song)
        song_name = selected_song['actual_name']
        loudness = selected_song['loudness']
        bpm = selected_song['bpm']
        key = selected_song['key']
        instruments = selected_song['instruments']

        song_url = f"https://uwipiyaoidfgmbjbsjuq.supabase.co/storage/v1/object/public/music/{genre.lower()}/{song_name}"
        print(song_url)

        return render_template('generate.html', song_url=song_url)
    else:
        return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)