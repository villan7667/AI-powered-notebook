#villan7667
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from transformers import T5ForConditionalGeneration, T5Tokenizer
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import re
import nltk
from collections import Counter
import logging
from bson import ObjectId
import json

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# MongoDB Configuration
MONGO_URI = "mongodb+srv://hsgf7667:villan7667@cluster7667.h95hy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster7667"
client = MongoClient(MONGO_URI)
db = client['ai_summary_notes']
users_collection = db['users']
summaries_collection = db['summaries']

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load model with error handling
try:
    model = T5ForConditionalGeneration.from_pretrained('t5-small')
    tokenizer = T5Tokenizer.from_pretrained("t5-small", use_fast=False)
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error(f"Error loading model: {e}")
    model = None
    tokenizer = None

def clean_text(text):
    """Clean and preprocess text"""
    text = re.sub(r'\s+', ' ', text.strip())
    text = re.sub(r'[^\w\s.,!?;:-]', '', text)
    return text

def extract_keywords(text, num_keywords=8):
    """Extract key words from text"""
    try:
        stop_words = set(stopwords.words('english'))
        words = word_tokenize(text.lower())
        words = [word for word in words if word.isalnum() and word not in stop_words and len(word) > 2]
        return [word for word, count in Counter(words).most_common(num_keywords)]
    except:
        return []

def get_text_stats(text):
    """Get text statistics"""
    try:
        sentences = sent_tokenize(text)
        words = word_tokenize(text)
        return {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'character_count': len(text),
            'avg_words_per_sentence': round(len(words) / len(sentences), 1) if sentences else 0
        }
    except:
        return {'word_count': 0, 'sentence_count': 0, 'character_count': 0, 'avg_words_per_sentence': 0}

def summarize(text, summary_type='balanced'):
    """Enhanced summarization with different types"""
    if not model or not tokenizer:
        return "Model not available. Please check the installation."
    
    try:
        text = clean_text(text)
        
        if summary_type == 'brief':
            max_length, min_length = 100, 20
            length_penalty = 2.5
        elif summary_type == 'detailed':
            max_length, min_length = 200, 60
            length_penalty = 1.5
        else:  # balanced
            max_length, min_length = 150, 40
            length_penalty = 2.0
        
        input_text = "summarize: " + text
        inputs = tokenizer.encode(input_text, return_tensors='pt', max_length=512, truncation=True)
        
        summary_ids = model.generate(
            inputs, 
            max_length=max_length, 
            min_length=min_length, 
            length_penalty=length_penalty, 
            num_beams=4, 
            early_stopping=True,
            do_sample=True,
            temperature=0.7
        )
        
        return tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    except Exception as e:
        logger.error(f"Summarization error: {e}")
        return f"Error generating summary: {str(e)}"

def save_summary_to_db(user_id, original_text, summary, summary_type, keywords, stats):
    """Save summary to MongoDB"""
    try:
        summary_doc = {
            'user_id': ObjectId(user_id),
            'original_text': original_text,
            'summary': summary,
            'summary_type': summary_type,
            'keywords': keywords,
            'stats': stats,
            'created_at': datetime.utcnow(),
            'title': original_text[:50] + '...' if len(original_text) > 50 else original_text
        }
        result = summaries_collection.insert_one(summary_doc)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Database save error: {e}")
        return None

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        user = users_collection.find_one({'email': email})
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            session['email'] = user['email']
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
    
    return render_template('auth.html', mode='login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # Check if user already exists
        if users_collection.find_one({'email': email}):
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        # Create new user
        user_doc = {
            'username': username,
            'email': email,
            'password': generate_password_hash(password),
            'created_at': datetime.utcnow(),
            'total_summaries': 0
        }
        
        result = users_collection.insert_one(user_doc)
        session['user_id'] = str(result.inserted_id)
        session['username'] = username
        session['email'] = email
        
        return jsonify({'success': True, 'message': 'Registration successful'})
    
    return render_template('auth.html', mode='register')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/summarize', methods=['POST'])
def summarize_text():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        summary_type = data.get('type', 'balanced')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        if len(text) < 50:
            return jsonify({'error': 'Text too short for meaningful summarization'}), 400
        
        # Generate summary
        summary = summarize(text, summary_type)
        keywords = extract_keywords(text)
        stats = get_text_stats(text)
        summary_stats = get_text_stats(summary)
        
        compression_ratio = round((1 - len(summary) / len(text)) * 100, 1) if text else 0
        
        # Save to database
        summary_id = save_summary_to_db(
            session['user_id'], 
            text, 
            summary, 
            summary_type, 
            keywords, 
            {**stats, **summary_stats, 'compression_ratio': compression_ratio}
        )
        
        # Update user's summary count
        users_collection.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$inc': {'total_summaries': 1}}
        )
        
        return jsonify({
            'summary': summary,
            'keywords': keywords,
            'original_stats': stats,
            'summary_stats': summary_stats,
            'compression_ratio': compression_ratio,
            'summary_id': summary_id
        })
        
    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/history')
def get_history():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    try:
        summaries = list(summaries_collection.find(
            {'user_id': ObjectId(session['user_id'])},
            {'original_text': 1, 'summary': 1, 'title': 1, 'created_at': 1, 'summary_type': 1, 'keywords': 1}
        ).sort('created_at', -1).limit(20))
        
        # Convert ObjectId to string for JSON serialization
        for summary in summaries:
            summary['_id'] = str(summary['_id'])
            summary['created_at'] = summary['created_at'].isoformat()
        
        return jsonify({'summaries': summaries})
    except Exception as e:
        logger.error(f"History fetch error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/delete_summary/<summary_id>', methods=['DELETE'])
def delete_summary(summary_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    try:
        result = summaries_collection.delete_one({
            '_id': ObjectId(summary_id),
            'user_id': ObjectId(session['user_id'])
        })
        
        if result.deleted_count > 0:
            return jsonify({'success': True, 'message': 'Summary deleted'})
        else:
            return jsonify({'error': 'Summary not found'}), 404
    except Exception as e:
        logger.error(f"Delete error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and file.filename.lower().endswith(('.txt', '.md')):
            try:
                content = file.read().decode('utf-8')
                return jsonify({'content': content, 'filename': file.filename})
            except UnicodeDecodeError:
                return jsonify({'error': 'File encoding not supported. Please use UTF-8.'}), 400
        else:
            return jsonify({'error': 'Only .txt and .md files are supported'}), 400
            
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    try:
        user = users_collection.find_one({'_id': ObjectId(session['user_id'])})
        summary_count = summaries_collection.count_documents({'user_id': ObjectId(session['user_id'])})
        
        # Get recent activity
        recent_summaries = list(summaries_collection.find(
            {'user_id': ObjectId(session['user_id'])},
            {'created_at': 1, 'summary_type': 1}
        ).sort('created_at', -1).limit(7))
        
        return jsonify({
            'username': user['username'],
            'email': user['email'],
            'total_summaries': summary_count,
            'member_since': user['created_at'].isoformat(),
            'recent_activity': [
                {
                    'date': s['created_at'].isoformat(),
                    'type': s['summary_type']
                } for s in recent_summaries
            ]
        })
    except Exception as e:
        logger.error(f"Profile error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
