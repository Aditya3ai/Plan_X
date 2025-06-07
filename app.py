from flask import Flask, render_template, request, redirect, url_for
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import DictCursor

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Image upload folder
UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# AWS RDS PostgreSQL configuration from environment variables
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '5432')

# Database connection function
def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        sslmode='require'
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        bride = request.form['bride']
        groom = request.form['groom']
        wedding_date = request.form['wedding_date']
        city = request.form['city']
        story = request.form.get('story', '')
        haldi = request.form.get('haldi_date') or None
        mehendi = request.form.get('mehendi_date') or None

        cover = request.files.get('cover_image')
        filename = None
        if cover and cover.filename:
            filename = f"{groom}-{bride}-{cover.filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            cover.save(filepath)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO wedding_details 
            (groom_name, bride_name, wedding_date, city, story, cover_image_path, haldi_date, mehendi_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (groom, bride, wedding_date, city, story, filename, haldi, mehendi))
        invite_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('invitation', invite_id=invite_id))

    return render_template('register.html')

@app.route('/invitation/<int:invite_id>')
def invitation(invite_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT * FROM wedding_details WHERE id = %s", (invite_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return "Invitation not found.", 404

    events = []
    if row['haldi_date']:
        events.append({'name': 'Haldi Ceremony', 'date': row['haldi_date']})
    if row['mehendi_date']:
        events.append({'name': 'Mehendi Ceremony', 'date': row['mehendi_date']})

    data = {
        'groom': row['groom_name'],
        'bride': row['bride_name'],
        'wedding_date': row['wedding_date'],
        'city': row['city'],
        'story': row['story'],
        'cover_image_path': row['cover_image_path'],
        'events': events
    }

    return render_template('invitation.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)
