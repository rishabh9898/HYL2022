from django.shortcuts import redirect, render
from flask import Flask, request, jsonify, make_response, send_from_directory, send_file, render_template, url_for
import os
import flask
from flask_cors import CORS
import pandas as pd
import numpy as np
import requests
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'studdybuddy'

CORS(app)
mysql = MySQL(app)

@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/result')
def result():
    return render_template('blog.html')

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