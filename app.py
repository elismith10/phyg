from flask import Flask, render_template, send_file, request, session, redirect
from diffusers import StableDiffusionPipeline
import torch
from PIL import Image
import io
import pandas as pd
from supabase import create_client, Client
import random
import zlib
import base64
from flask_session import Session

model_id = "CompVis/stable-diffusion-v1-4"
pipe = StableDiffusionPipeline.from_pretrained(model_id)
pipe = pipe.to("cpu")


app = Flask(__name__)
app.secret_key ='key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'app:'

Session(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    session.clear()
    genre = request.form.get('genre')
    custom_prompt = request.form.get('custom_prompt')
    if genre:
        print(genre)
        # Supabase authentification
        url = "https://uwipiyaoidfgmbjbsjuq.supabase.co"
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV3aXBpeWFvaWRmZ21iamJzanVxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjE0MDQ4NzksImV4cCI6MjAzNjk4MDg3OX0.UEfvSlN-FdAdwonkYEiaz5dLGwY7TSFQNkvR_08AHDk"
        client = create_client(url, key)

        response = client.table("songs").select("*").eq("genre", genre.lower()).execute()
        data = response.data

        df = pd.DataFrame(data)
        selected_song = df.sample(n=1).iloc[0]
        print(selected_song)

        song_name = selected_song['actual_name']
        pseudo_name = selected_song['pseudo_name']
        loudness = selected_song['loudness']
        bpm = selected_song['bpm']
        key = selected_song['key']
        instruments = selected_song['instruments']
        song_url = f"https://uwipiyaoidfgmbjbsjuq.supabase.co/storage/v1/object/public/music/{genre.lower()}/{song_name}"

        artists = [
            "Leonardo da Vinci", "Michelangelo", "Raphael", "Vincent van Gogh", "Pablo Picasso",
            "Claude Monet", "Salvador Dalí", "Frida Kahlo", "Andy Warhol", "Jackson Pollock",
            "Georgia O'Keeffe", "Rembrandt", "Johannes Vermeer", "Henri Matisse", "Edvard Munch",
            "Paul Cézanne", "Gustav Klimt", "Wassily Kandinsky", "Marcel Duchamp", "Jean-Michel Basquiat"
        ]
        selected_artist = random.choice(artists)

        # generate prompt
        if custom_prompt:
            print(custom_prompt)
            prompt = f"""
            Music features:
            - Key: {selected_song["key"]},
            - BPM: {selected_song["bpm"]},
            - Genre: {selected_song["genre"]},
            {custom_prompt}
            """
        else:
            prompt = f"Generate an artistic piece that represents the song '{pseudo_name}', loudness {loudness} dB, tempo {bpm} BPM, key {key}, featuring instruments {instruments}, inspired by {selected_artist}."
        print(prompt)
        
        image = pipe(prompt, num_inference_steps=1, height=16, width=16).images[0]
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', optimizer=True, compress_level=4)
        img_byte_arr.seek(0)
        
        image_b64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

        compressed = zlib.compress(img_byte_arr.getvalue())
        session['image_bytes'] = compressed
        session['genre'] = genre

        return render_template('generate.html', song_url=song_url, song_name=pseudo_name, image=image_b64)

    return render_template('index.html', error='Please select a genre')
    
@app.route('/download', methods=['POST'])
def download_image():
    if 'image_bytes' in session:
        compressed = session['image_bytes']
        image_bytes = zlib.decompress(compressed)
        genre = session.get('genre')
        
        img_byte_arr = io.BytesIO(image_bytes)
        img_byte_arr.seek(0)
        return send_file(img_byte_arr, mimetype='image/jpeg', as_attachment=True, download_name=f'{genre}.jpeg')
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)