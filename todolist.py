# This is a simple example web app that is meant to illustrate the basics.
from flask import Flask, render_template, redirect, g, request, url_for, session, jsonify
import googletrans
import sqlite3
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DATABASE = 'todolist.db'

EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_PASSWORD = "sdryjybuizrtujge"
EMAIL_HOST_USER = "almondpudding9@gmail.com"

languages = googletrans.LANGUAGES
abbrevations = {
  'SQ': 'Albanian',
  'AM': 'Amharic',
  'AR': 'Arabic',
  'HY': 'Armenian',
  'AS': 'Assamese',
  'AY': 'Aymara',
  'AZ': 'Azerbaijani',
  'BM': 'Bambara',
  'BA': 'Bashkir',
  'BE': 'Belarusian',
  'BN': 'Bengali',
  'BH': 'Bihari',
  'BS': 'Bosnian',
  'BG': 'Bulgarian',
  'CA': 'Catalan',
  'CEB': 'Cebuano',
  'ZH-CN': 'Chinese (Simplified)',
  'ZH-TW': 'Chinese (Traditional)',
  'CO': 'Corsican',
  'HR': 'Croatian',
  'CS': 'Czech',
  'DA': 'Danish',
  'DV': 'Dhivehi',
  'DZ': 'Dzongkha',
  'NL': 'Dutch',
  'EN': 'English',
  'EO': 'Esperanto',
  'ET': 'Estonian',
  'TL': 'Filipino',
  'FI': 'Finnish',
  'FR': 'French',
  'GL': 'Galician',
  'KA': 'Georgian',
  'DE': 'German',
  'EL': 'Greek',
  'GU': 'Gujarati',
  'HT': 'Haitian Creole',
  'HA': 'Hausa',
  'HE': 'Hebrew',
  'HI': 'Hindi',
  'HU': 'Hungarian',
  'IS': 'Icelandic',
  'ID': 'Indonesian',
  'GA': 'Irish',
  'IT': 'Italian',
  'JA': 'Japanese',
  'KN': 'Kannada',
  'KK': 'Kazakh',
  'KM': 'Khmer',
  'KO': 'Korean',
  'KY': 'Kyrgyz',
  'LO': 'Lao',
  'LT': 'Lithuanian',
  'LV': 'Latvian',
  'MK': 'Macedonian',
  'MG': 'Malagasy',
  'ML': 'Malayalam',
  'MT': 'Maltese',
  'MR': 'Marathi',
  'MN': 'Mongolian',
  'MY': 'Myanmar (Burmese)',
  'NE': 'Nepali',
  'NO': 'Norwegian',
  'OM': 'Oromo',
  'OR': 'Oriya',
  'PS': 'Pashto',
  'FA': 'Persian',
  'PL': 'Polish',
  'PT': 'Portuguese',
  'PA': 'Punjabi',
  'RO': 'Romanian',
  'RU': 'Russian',
  'SA': 'Sanskrit',
  'SI': 'Slovenian',
  'SK': 'Slovak',
  'SL': 'Slovenian'
}
language_dict = {}
for language in languages:
  if language.upper() in abbrevations:
    language_dict[abbrevations[language.upper()]] = language

app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

def translate_text(text, language):
  """Translates the given text to the specified language.

  Args:
    text: The text to translate.
    language: The language to translate to.

  Returns:
    The translated text.
  """

  translator = googletrans.Translator()
  return translator.translate(text, dest=language).text

def send_email(text, subject, to_email):
    # Set up the SMTP server
    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
    server.starttls()
    server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)

    # Create a message
    msg = MIMEMultipart()
    msg['From'] = EMAIL_HOST_USER
    msg['To'] = to_email
    msg['Subject'] = subject

    # Add body to email
    body = MIMEText(text)
    msg.attach(body)

    # Send the message
    server.sendmail(EMAIL_HOST_USER, to_email, msg.as_string())

    # Close the SMTP server
    server.quit()


@app.route('/set_email', methods=['POST'])
def set_session_data():
    data = request.json # assuming data is sent as JSON
    session['email'] = data['email']
    return jsonify({'message': 'Email set successfully'})

@app.route("/")
def show_list():
    db = get_db()
    cur = db.execute('SELECT what_to_do, due_date, status FROM entries')
    entries = cur.fetchall()
    tdlist = [dict(what_to_do=row[0], due_date=row[1], status=row[2])
              for row in entries]
    return render_template('index.html', todolist=tdlist, language_dict=language_dict)


@app.route("/add", methods=['POST'])
def add_entry():
    db = get_db()
    language = request.form['language']
    what_to_do = request.form['what_to_do']
    due_date = request.form['due_date']
    try:
        translated = translate_text(what_to_do, language)
    except:
        translated = what_to_do
    db.execute('insert into entries (what_to_do, due_date) values (?, ?)',
               [translated, due_date])
    db.commit()
    send_email("Your task "+translated+" is added!", "Task added", session['email'])
    return redirect(url_for('show_list'))


@app.route("/delete/<item>")
def delete_entry(item):
    db = get_db()
    db.execute("DELETE FROM entries WHERE what_to_do='"+item+"'")
    db.commit()
    send_email("Your task "+item+" is deleted!", "Task deleted", session['email'])
    return redirect(url_for('show_list'))


@app.route("/mark/<item>")
def mark_as_done(item):
    db = get_db()
    db.execute("UPDATE entries SET status='done' WHERE what_to_do='"+item+"'")
    db.commit()
    send_email("Your task "+item+" is done!", "Task done", session['email'])
    return redirect(url_for('show_list'))

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = sqlite3.connect(app.config['DATABASE'])
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


if __name__ == "__main__":
    app.run(debug=True, port=5002)
