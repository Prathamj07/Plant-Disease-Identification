from flask import Flask, request, render_template, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import bcrypt
import cv2
import numpy as np
from keras.models import load_model
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = 'secret_key'


working_dir = os.path.dirname(os.path.abspath(__file__))
new_model = load_model("plant_disease\\plant_disease_prediction_model.h5")
new_class_indices = json.load(open(os.path.join(working_dir, "class_indices.json")))


# Predection Fuction
def predict_disease_new(image_path):

    image = cv2.imread(image_path)
    image = cv2.resize(image, (224, 224))  
    image = image / 255.0  
    image = np.expand_dims(image, axis=0) 

    predictions = new_model.predict(image)
    predicted_class_index = np.argmax(predictions, axis=1)[0]
    predicted_class_name = new_class_indices[str(predicted_class_index)]
    confidence = predictions[0][predicted_class_index]

    return predicted_class_name, confidence

#Database

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    
    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_path = db.Column(db.String(300), nullable=False)
    predicted_class = db.Column(db.String(100), nullable=False)
    confidence = db.Column(db.Float, nullable=False)

    user = db.relationship('User', backref=db.backref('predictions', lazy=True))

    def __init__(self, user_id, image_path, predicted_class, confidence):
        self.user_id = user_id
        self.image_path = image_path
        self.predicted_class = predicted_class
        self.confidence = confidence
        
#Routes

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['email'] = user.email
            return redirect('/upload')
        else:
            return render_template('index.html', error='Invalid User, Kindly register!', error_type='login')
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user:
            return render_template('index.html', error='User already exists, please login.', error_type='register')

        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'image' not in request.files:
            return jsonify({'message': 'No file part'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'message': 'No selected file'}), 400

        if file:
            
            counter_file_path = os.path.join(working_dir, 'image_counter.txt')
            if os.path.exists(counter_file_path):
                with open(counter_file_path, 'r') as counter_file:
                    counter = int(counter_file.read().strip())
            else:
                counter = 1

            #Uploaded Image Name
            filename = f'image_{counter:05d}.jpg'  # Example: image_00001.jpg
            file_path = os.path.join('uploads', filename)
            os.makedirs('uploads', exist_ok=True)
            file.save(file_path)

            
            with open(counter_file_path, 'w') as counter_file:
                counter_file.write(str(counter + 1))

            # Predection 
            predicted_class, confidence = predict_disease_new(file_path)
            confidence = float(confidence)

            # Store the prediction in the database
            if 'email' in session:
                user = User.query.filter_by(email=session['email']).first()
                if user:
                    new_prediction = Prediction(user_id=user.id, image_path=file_path, predicted_class=predicted_class, confidence=confidence)
                    db.session.add(new_prediction)
                    db.session.commit()
            
            return jsonify({'predicted_class': predicted_class, 'confidence': confidence}), 200
        else:
            return jsonify({'message': 'Invalid file format'}), 400
    return render_template('upload.html')

@app.route('/logout')
def logout():
    session.pop('email', None)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
