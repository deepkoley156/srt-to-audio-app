import os
import re
import asyncio
from flask import Flask, render_template, request, send_file, redirect, url_for
import edge_tts

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def parse_srt(file_path):
    """SRT বা VTT ফাইল থেকে শুধুমাত্র টেক্সটগুলো বের করে একটি পরিষ্কার স্ট্রিং বানানোর ফাংশন"""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # SRT টাইমকোড এবং নাম্বার রিমুভ করার রেজেক্স
    # যেমন: 00:00:01,000 --> 00:00:04,000 এবং সংখ্যাগুলো বাদ দেওয়া
    text_content = re.sub(r'\d+\n\d\d:\d\d:\d\d[,\.]\d\d\d --> \d\d:\d\d:\d\d[,\.]\d\d\d.*\n', '', content)
    text_content = re.sub(r'^\d+\s*$', '', text_content, flags=re.MULTILINE)
    
    # অতিরিক্ত খালি লাইন ও স্পেস দূর করা
    lines = [line.strip() for line in text_content.splitlines() if line.strip()]
    return " ".join(lines)

async def text_to_speech(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    if 'srt_file' not in request.files:
        return redirect(url_for('index'))
    
    file = request.files['srt_file']
    voice = request.form.get('voice', 'en-US-AriaNeural')
    
    if file.filename == '':
        return redirect(url_for('index'))
    
    if file:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        
        # SRT থেকে টেক্সট এক্সট্রাক্ট করা
        extracted_text = parse_srt(file_path)
        
        if not extracted_text:
            return "Error: Could not extract text from the subtitle file.", 400
        
        output_filename = os.path.splitext(file.filename)[0] + '_audio.mp3'
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        # এজ টিটিএস রান করা
        asyncio.run(text_to_speech(extracted_text, voice, output_path))
        
        return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)