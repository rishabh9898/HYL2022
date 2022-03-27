# from django.shortcuts import redirect, render
from flask import Flask, request, jsonify, make_response, send_from_directory, send_file, render_template, url_for
import os
import flask
from flask_cors import CORS
import pandas as pd
import numpy as np
import requests
from flask_mysqldb import MySQL
import re
import PyPDF2
from PyPDF2 import PdfFileReader
import string
import json
import requests
from googleapiclient.discovery import build

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'studdybuddy'
API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
API_TOKEN = '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'

headers = {"Authorization": f"Bearer {API_TOKEN}"}

CORS(app)
mysql = MySQL(app)

titleGiven = ""
def query(payload):
    data = json.dumps(payload)
    response = requests.request("POST", API_URL, headers=headers, data=data)
    return json.loads(response.content.decode("utf-8"))

def preprocess (text):
  str_punctuation=string.punctuation.replace('.','')
  text=text.lower()
  text = re.sub(r'^https?://.[\r\n]', '', text, flags=re.MULTILINE)
  #text = text.translate(str.maketrans('', '', str_punctuation))
  text=" ".join(filter(lambda x:x[0]!='[', text.split()))
  text = text.replace('\n','')
  text= text.replace('\t','')
  text=re.sub(' +', ' ', text)
  return text

def youtube(query):
    # api_key = "AIzaSyDWWErzd2qUj0uh-N7123d7hvuQkKjMGh4"
    api_key = "AIzaSyDhs3vS_OwXut_S2AxXE1AOYid9Emd3iSo"
    youtube = build('youtube', 'v3', developerKey=api_key)
    type(youtube)
    req = youtube.search().list(q=query, part='snippet')
    result = req.execute()

    titles = []
    links = []
    descriptions = []
    channel = []
    publishtime = []
    result1 = []

    for i in range(0, len(result['items'])):
        titles.append(result['items'][i]['snippet']['title'])
        links.append("https://www.youtube.com/embed/"+result['items'][i]['id']['videoId'])
        descriptions.append(result['items'][i]['snippet']['description'])
        channel.append(result['items'][i]['snippet']['channelTitle'])
        publishtime.append(result['items'][i]['snippet']['publishTime'])
    

    for i in range(0, len(result['items'])):
        result1.append({'title': titles[i], 'abstract': descriptions[i], 'url': links[i], 'channelname' : channel[i],'publishtime' : publishtime[i]})


    return result1



@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/results', methods = ['GET', 'POST'])
def results():
    if request.method == 'POST':
      f = request.files['file']
      fileType = f.filename.rsplit('.', 1)[1].lower()
      pdf = PyPDF2.PdfFileReader(f)
      num_pages= pdf.getNumPages()
      text=''
      for i in range(num_pages):
        page=pdf.getPage(i)
        text=text+page.extractText()
    
      print(type(f))
      text = preprocess(text)
      print(num_pages)
      print(text)
    #   return 'file uploaded successfully'
    titleGiven = query({
                    "inputs":text, "parameters": {"do_sample": False ,"min_length":5 ,"max_length": 10},
                })

    


    summaryGiven = query({
                    "inputs":text, "parameters": {"do_sample": False ,"min_length":250 ,"max_length": 300},
                })

    # cur0 = mysql.connection.cursor()
    # mysql.connection.commit()
    # cur0.close()

    # cur = mysql.connection.cursor()
    # cur.execute("""UPDATE USERCREDENTIALS SET Queries = %s WHERE username = %s""", (titleGiven['summary_text'],""))
    # mysql.connection.commit()
    # cur.close()

    wordSummary = {}
    wordSummary['summary'] = summaryGiven[0]['summary_text']
    wordTitle = {}
    wordTitle['title'] = titleGiven[0]['summary_text']

    res = youtube(titleGiven)
    size = len(res)

    url = []
    abstract = []
    title = []
    publishTime = []
    channel = []

    
    for i in range(3):

         url.append(res[i]['url'])
         title.append(res[i]['title'])
         abstract.append(res[i]['abstract'])
         match = re.search(r'(\d+-\d+-\d+)',res[i]['publishtime'])
         publishTime.append(match.group(1))
         channel.append(res[i]['channelname'])
    # return url[0]
    return render_template('blogold.html',
    wordTitle = wordTitle,
    wordSummary=wordSummary,
    url=url,
    abstract = abstract,
    title = title,
    publishTime = publishTime,
    channel = channel,
    length = 3
    )


@app.route('/search')
def search():
    return render_template('search.html')

@app.route('/portal')
def portal():
    return render_template('portal.html')

@app.route('/signup', methods = ['POST', 'GET'])
def signup():

    print("signup")

    name = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    cur0 = mysql.connection.cursor()
    result = cur0.execute("Select * FROM USERCREDENTIALS")

    if (result > 0):
        userDetails = cur0.fetchall()
        for user in userDetails:
            if (user[1] == email or user[0] == name):
                return jsonify({'status':'user already exists.'}), 500

    mysql.connection.commit()
    cur0.close()

    cur = mysql.connection.cursor()
    cur.execute("""INSERT INTO USERCREDENTIALS(email,username, password) VALUES(%s,%s,%s)""", (email, name ,password))
    mysql.connection.commit()
    cur.close()

    result = {"username": name, "email": email, "password": password}


    return jsonify(result), 200
    

@app.route('/signin', methods = ['POST'])
def signin():


    email = request.form.get("email")
    password = request.form.get("password")

    cur = mysql.connection.cursor()
    result = cur.execute("Select * FROM USERCREDENTIALS")

    if(result>0):

        userDetails = cur.fetchall()
        for user in userDetails:
            if(user[1]==email and user[2]==password):
                print("user is " +str(user[0]))
                result = {'username': user[0], "email":user[1], "password":user[2]}
                return jsonify(result), 200

    return jsonify({'error':'No valid account found!'}), 200
   



if __name__ == "__main__":
    app.run(debug=True)