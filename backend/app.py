from __future__ import annotations
import hashlib, hmac, json, os, re, secrets, sqlite3, urllib.request
from datetime import date, timedelta
from contextlib import contextmanager
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BASE_DIR=Path(__file__).resolve().parent
FRONTEND_DIR=Path(os.getenv('UDAAN_FRONTEND_DIR',str(BASE_DIR.parent/'frontend'/'dist'))).resolve()
DB_PATH=Path(os.getenv('DATABASE_PATH',str(BASE_DIR/'learning.db')))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
app=FastAPI(title='Udaan Primary Learning API',version='2.0.0',description='Grades 1–5, English/Hindi/Tamil, assignments, parent progress and teacher tools')
app.add_middleware(CORSMiddleware,allow_origins=os.getenv('CORS_ORIGINS','http://localhost:5173,http://127.0.0.1:5173').split(','),allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
SESSIONS={}
def password_hash(password,salt=None):
    salt=salt or secrets.token_hex(16); return f'{salt}${hashlib.pbkdf2_hmac("sha256",password.encode(),salt.encode(),120000).hex()}'
def password_matches(password,stored):
    try:
        salt,expected=stored.split('$',1); return hmac.compare_digest(hashlib.pbkdf2_hmac('sha256',password.encode(),salt.encode(),120000).hex(),expected)
    except ValueError:return False
@contextmanager
def db():
    c=sqlite3.connect(DB_PATH); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON')
    try: yield c; c.commit()
    finally:c.close()
def add_column(c,table,column,definition):
    if column not in [r['name'] for r in c.execute(f'PRAGMA table_info({table})')]: c.execute(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')
def init_db():
    with db() as c:
        c.executescript('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL,role TEXT NOT NULL,password_hash TEXT NOT NULL,grade INTEGER DEFAULT 3,student_id INTEGER,FOREIGN KEY(student_id) REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS lessons(id INTEGER PRIMARY KEY AUTOINCREMENT,title_en TEXT NOT NULL,title_hi TEXT NOT NULL,subject TEXT NOT NULL,grade INTEGER NOT NULL,body_en TEXT NOT NULL,body_hi TEXT NOT NULL,published INTEGER NOT NULL DEFAULT 1,created_by INTEGER,picture TEXT NOT NULL DEFAULT '🌈',FOREIGN KEY(created_by) REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS questions(id INTEGER PRIMARY KEY AUTOINCREMENT,lesson_id INTEGER NOT NULL,prompt_en TEXT NOT NULL,prompt_hi TEXT NOT NULL,options_en TEXT NOT NULL,options_hi TEXT NOT NULL,correct_index INTEGER NOT NULL,explanation_en TEXT NOT NULL,explanation_hi TEXT NOT NULL,FOREIGN KEY(lesson_id) REFERENCES lessons(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,lesson_id INTEGER NOT NULL,score INTEGER NOT NULL,total INTEGER NOT NULL,answers TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(user_id) REFERENCES users(id),FOREIGN KEY(lesson_id) REFERENCES lessons(id));
        CREATE TABLE IF NOT EXISTS assignments(id INTEGER PRIMARY KEY AUTOINCREMENT,lesson_id INTEGER NOT NULL,student_id INTEGER NOT NULL,teacher_id INTEGER NOT NULL,due_date TEXT DEFAULT '',note TEXT DEFAULT '',created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(lesson_id) REFERENCES lessons(id) ON DELETE CASCADE,FOREIGN KEY(student_id) REFERENCES users(id),FOREIGN KEY(teacher_id) REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS attendance(id INTEGER PRIMARY KEY AUTOINCREMENT,student_id INTEGER NOT NULL,attendance_date TEXT NOT NULL,status TEXT NOT NULL CHECK(status IN ('Present','Absent')),UNIQUE(student_id,attendance_date),FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS reward_events(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,activity_key TEXT NOT NULL,event_day TEXT NOT NULL,stars INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,UNIQUE(user_id,activity_key,event_day),FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE);''')
        add_column(c,'lessons','title_ta',"TEXT NOT NULL DEFAULT ''"); add_column(c,'lessons','body_ta',"TEXT NOT NULL DEFAULT ''"); add_column(c,'lessons','picture',"TEXT NOT NULL DEFAULT '🌈'")
        add_column(c,'questions','prompt_ta',"TEXT NOT NULL DEFAULT ''"); add_column(c,'questions','options_ta',"TEXT NOT NULL DEFAULT '[]'"); add_column(c,'questions','explanation_ta',"TEXT NOT NULL DEFAULT ''")
        add_column(c,'users','grade','INTEGER DEFAULT 3'); add_column(c,'users','student_id','INTEGER'); add_column(c,'users','class_name',"TEXT NOT NULL DEFAULT ''"); add_column(c,'users','roll_number',"TEXT NOT NULL DEFAULT ''"); add_column(c,'users','stars','INTEGER NOT NULL DEFAULT 0'); add_column(c,'users','avatar',"TEXT NOT NULL DEFAULT 'astro'"); add_column(c,'lessons','visuals_json',"TEXT NOT NULL DEFAULT '[]'")
        if c.execute('SELECT COUNT(*) FROM users').fetchone()[0]==0:
            c.execute('INSERT INTO users(name,email,role,password_hash,grade) VALUES(?,?,?,?,?)',('Demo Teacher','teacher@demo.com','teacher',password_hash('teacher123'),None))
            c.execute('INSERT INTO users(name,email,role,password_hash,grade) VALUES(?,?,?,?,?)',('Aarav Student','student@demo.com','student',password_hash('student123'),3))
            sid=c.execute("SELECT id FROM users WHERE role='student'").fetchone()[0]
            c.execute('INSERT INTO users(name,email,role,password_hash,student_id) VALUES(?,?,?,?,?)',('Demo Parent','parent@demo.com','parent',password_hash('parent123'),sid))
        else:
            if not c.execute("SELECT id FROM users WHERE email='parent@demo.com'").fetchone():
                sid=c.execute("SELECT id FROM users WHERE role='student' ORDER BY id LIMIT 1").fetchone()
                c.execute('INSERT INTO users(name,email,role,password_hash,student_id) VALUES(?,?,?,?,?)',('Demo Parent','parent@demo.com','parent',password_hash('parent123'),sid[0] if sid else None))
        # Demo identities for all 5 grade-specific student portals + linked parents.
        teacher_row=c.execute("SELECT id FROM users WHERE role='teacher' ORDER BY id LIMIT 1").fetchone()
        if not teacher_row:
            c.execute('INSERT INTO users(name,email,role,password_hash,grade) VALUES(?,?,?,?,?)',('Grade 3 Teacher','teacher@demo.com','teacher',password_hash('teacher123'),3))
        c.execute("UPDATE users SET grade=3 WHERE email='teacher@demo.com' AND role='teacher'")
        for g in range(1,6):
            student_email='student@demo.com' if g==3 else f'grade{g}@demo.com'
            sr=c.execute('SELECT id FROM users WHERE lower(email)=lower(?)',(student_email,)).fetchone()
            if not sr:
                c.execute('INSERT INTO users(name,email,role,password_hash,grade) VALUES(?,?,?,?,?)',(f'Grade {g} Demo Student',student_email,'student',password_hash('student123' if g==3 else 'learn123'),g))
                sr=c.execute('SELECT id FROM users WHERE lower(email)=lower(?)',(student_email,)).fetchone()
            else:
                c.execute("UPDATE users SET grade=? WHERE id=? AND role='student'",(g,sr['id']))
            parent_email=f'parent{g}@demo.com'
            if not c.execute('SELECT id FROM users WHERE lower(email)=lower(?)',(parent_email,)).fetchone():
                c.execute('INSERT INTO users(name,email,role,password_hash,student_id) VALUES(?,?,?,?,?)',(f'Grade {g} Demo Parent',parent_email,'parent',password_hash('parent123'),sr['id']))
        grade3=c.execute("SELECT id FROM users WHERE role='student' AND grade=3 ORDER BY id LIMIT 1").fetchone()
        if grade3:
            c.execute("UPDATE users SET student_id=? WHERE email='parent@demo.com'",(grade3['id'],))
        if c.execute('SELECT COUNT(*) FROM lessons').fetchone()[0]<75:
            teacher=c.execute("SELECT id FROM users WHERE role='teacher' LIMIT 1").fetchone()[0]
            subjects=['English','Mathematics','Science','Social Studies','Tamil']
            lesson_templates={
              'English':[('Story Detectives','Stories have characters, settings and events. Look for clues about who is speaking, where the story happens and what changes. Retell events in order using first, next and finally.'),('Word Builders','Words can have similar or opposite meanings. Use the whole sentence as a clue, then choose the word that makes the meaning clear.'),('Writing Workshop','A good paragraph has one main idea, supporting details and a closing sentence. Read your work aloud and check capitals, punctuation and spelling.')],
              'Mathematics':[('Number Explorers','Numbers can be grouped, compared and broken apart. Use place value to explain why a number is greater or smaller, not just how it looks.'),('Patterns and Puzzles','A pattern follows a rule. Compare neighbouring items, state the rule in words and test it on the next item before deciding your answer.'),('Shapes in Action','Shapes have properties such as sides, corners and symmetry. Describe a shape using its properties instead of relying only on its colour or size.')],
              'Science':[('Living Things','Living things grow and need resources. Observe carefully, compare evidence and explain how a feature helps an organism survive in its environment.'),('Matter Detectives','Materials have properties such as texture, flexibility and ability to absorb water. Choose a fair test and change only one factor at a time.'),('Earth and Sky','The Sun provides light and warmth. Shadows change when the position of a light source or object changes; observations help us describe the pattern.')],
              'Social Studies':[('Our Community','Communities include people who help one another in different ways. Maps, symbols and directions help us understand places and how people connect.'),('Past and Present','We learn about the past using evidence such as objects, photographs, stories and records. Compare sources and ask who made them and why.'),('Nature and Resources','Natural resources support life. Reduce waste, reuse useful items and protect shared spaces so resources remain available for others.')],
              'Tamil':[('Word Meaning','Words express ideas and feelings. Use the surrounding sentence to work out a word’s meaning and notice how a word changes a sentence.'),('Story Order','Stories have characters, places and events. Put events in a sensible order and explain how the beginning leads to the ending.'),('Nature Vocabulary','Tamil words can describe trees, birds, animals and the world around us. Use clear words to explain how we can care for nature.')]
            }
            tamil_title=['சொல் உலகம்','எண்ணங்களின் விளையாட்டு','அறிவியல் ஆர்வம்']
            titles_hi={'English':['कहानी के सुराग','शब्दों की खोज','वाक्य बनाने की कला'],'Mathematics':['संख्या सफ़ारी','पैटर्न खोजी','आकार प्रयोगशाला'],'Science':['पौधों की ताकत','पदार्थों की जाँच','मौसम और छाया'],'Social Studies':['हमारा समुदाय','नक्शा बनाना सीखें','धरती के रखवाले'],'Tamil':['तमिल शब्द खेल','कहानी का क्रम','प्रकृति की दुनिया']}
            titles_ta={'English':['கதைத் தடயங்கள்','சொற்களை ஆராய்வோம்','வாக்கியம் அமைப்போம்'],'Mathematics':['எண்கள் உலா','வடிவமைப்பைக் கண்டுபிடி','வடிவங்களின் ஆய்வகம்'],'Science':['தாவரங்களின் ஆற்றல்','பொருட்களை ஆராய்வோம்','வானிலையும் நிழலும்'],'Social Studies':['நமது சமூகம்','வரைபடம் வரைவோம்','பூமியைப் பாதுகாப்போம்'],'Tamil':['சொற்களின் விளையாட்டு','கதையின் வரிசை','இயற்கை உலகம்']}
            body_hi_map={
              'English':['कहानी में पात्र, स्थान और घटनाएँ पहचानें। शुरुआत, बीच और अंत के संकेतों से घटनाओं का सही क्रम बनाएँ।','वाक्य के संदर्भ से शब्द का अर्थ समझें। समानार्थी और विपरीत अर्थ वाले शब्द पहचानकर सही शब्द चुनें।','एक अच्छे वाक्य में स्पष्ट विचार, सही शब्द और विराम-चिह्न होते हैं। वाक्य पढ़कर देखें कि अर्थ पूरा है या नहीं।'],
              'Mathematics':['संख्याओं को समूहों में बाँटें और स्थान-मूल्य समझें। चित्र में समूह गिनकर कुल संख्या और तुलना का कारण बताएँ।','संख्या या चित्रों में दोहराए जाने वाले नियम को पहचानें। अगले पद का अनुमान लगाएँ और नियम से जाँचें।','आकारों की भुजाएँ, कोने और सममिति देखें। केवल रंग नहीं, गुणों के आधार पर आकार पहचानें।'],
              'Science':['पौधों को बढ़ने के लिए पानी, हवा और प्रकाश चाहिए। चित्र में जड़, तना और पत्तियों के काम को पहचानें।','वस्तुओं की कठोरता, लचीलेपन और पानी सोखने की क्षमता की तुलना करें। निष्पक्ष जाँच में एक समय पर एक चीज़ बदलें।','सूर्य प्रकाश और गर्मी देता है। प्रकाश की दिशा बदलने पर छाया में होने वाले बदलाव को देखकर कारण समझाएँ।'],
              'Social Studies':['समुदाय में लोग अलग-अलग काम करके एक-दूसरे की मदद करते हैं। किसी व्यक्ति के काम को उससे मिलने वाली सेवा से जोड़ें।','अतीत को समझने के लिए तस्वीरें, वस्तुएँ और कहानियाँ प्रमाण दे सकती हैं। स्रोत को ध्यान से देखकर पूछें कि वह क्या बताता है।','पानी, पेड़ और मिट्टी जैसे प्राकृतिक संसाधनों की रक्षा करें। कम उपयोग और पुनः उपयोग से संसाधन बचते हैं।'],
              'Tamil':['तमिल शब्द हमारे विचार और भाव व्यक्त करते हैं। वाक्य के संदर्भ से शब्द का अर्थ पहचानें और सही शब्द चुनें।','कहानी में पात्र, स्थान और घटनाएँ होती हैं। घटनाओं को सही क्रम में रखकर शुरुआत और अंत का संबंध समझाएँ।','तमिल में प्रकृति से जुड़े शब्दों का उपयोग करके पेड़-पौधों और जानवरों का वर्णन करें। पर्यावरण की रक्षा के तरीके बताएँ।']}
            body_ta_map={
              'English':['கதையில் வரும் பாத்திரங்கள், இடம், நிகழ்வுகளை அடையாளம் காணுங்கள். தொடக்கம், நடுப்பு, முடிவு ஆகிய குறிப்புகளால் நிகழ்வுகளை வரிசைப்படுத்துங்கள்.','வாக்கியச் சூழலைக் கொண்டு சொல்லின் பொருளைக் கண்டறியுங்கள். ஒரே பொருள் அல்லது எதிர்ப்பொருள் தரும் சொற்களை வேறுபடுத்துங்கள்.','தெளிவான வாக்கியத்தில் முழுமையான கருத்தும் சரியான சொற்களும் நிறுத்தக்குறிகளும் இருக்கும். வாக்கியத்தை வாசித்து சரிபாருங்கள்.'],
              'Mathematics':['எண்களை எண்ணி இடமதிப்பைப் புரிந்துகொள்ளுங்கள். படத்தில் உள்ள குழுக்களைப் பார்த்து மொத்தத்தையும் ஒப்பீட்டையும் விளக்குங்கள்.','எண்கள் அல்லது படங்களில் மீண்டும் வரும் விதியைக் கண்டறிந்து அடுத்ததை கணித்து விதியால் சரிபாருங்கள்.','வடிவங்களின் பக்கங்கள், மூலைகள், சமச்சீர் ஆகியவற்றைக் கவனியுங்கள். நிறத்தை விட பண்புகளால் வடிவத்தை அடையாளம் காணுங்கள்.'],
              'Science':['தாவரங்கள் வளர நீர், காற்று, ஒளி தேவை. படத்தில் வேர், தண்டு, இலை ஆகியவற்றின் பணிகளை அடையாளம் காணுங்கள்.','கடினத்தன்மை, நெகிழ்வு, நீரை உறிஞ்சுதல் போன்ற பண்புகளால் பொருட்களை ஒப்பிடுங்கள். நியாயமான சோதனையில் ஒரே ஒரு காரணியை மாற்றுங்கள்.','சூரியன் ஒளியும் வெப்பமும் தருகிறது. ஒளியின் திசை மாறும்போது நிழலில் ஏற்படும் மாற்றத்தை கவனித்து காரணம் கூறுங்கள்.'],
              'Social Studies':['சமூகத்தில் மக்கள் பல்வேறு பணிகள் மூலம் ஒருவருக்கொருவர் உதவுகிறார்கள். ஒரு பணியை அதனால் கிடைக்கும் சேவையுடன் பொருத்துங்கள்.','புகைப்படங்கள், பொருட்கள், கதைகள் கடந்தகாலத்தைப் பற்றிய ஆதாரங்களைத் தருகின்றன. அவற்றை கவனித்து என்ன தெரிகிறது எனக் கூறுங்கள்.','நீர், மரங்கள், மண் போன்ற இயற்கை வளங்களைப் பாதுகாக்க வேண்டும். குறைவாகப் பயன்படுத்துதல் மற்றும் மீண்டும் பயன்படுத்துதல் வளங்களைச் சேமிக்கும்.'],
              'Tamil':['தமிழ்ச் சொற்கள் நம் எண்ணங்களையும் உணர்வுகளையும் வெளிப்படுத்துகின்றன. வாக்கியச் சூழலைக் கொண்டு சொல்லின் பொருளைக் கண்டறியுங்கள்.','கதையில் பாத்திரங்கள், இடம், நிகழ்வுகள் இருக்கும். நிகழ்வுகளை சரியான வரிசையில் அமைத்து தொடக்கமும் முடிவும் எவ்வாறு இணைகின்றன என விளக்குங்கள்.','இயற்கையைக் குறிக்கும் தமிழ்ச் சொற்களால் மரங்கள், தாவரங்கள், விலங்குகளை விவரியுங்கள். சுற்றுச்சூழலைப் பாதுகாக்கும் வழிகளைச் சொல்லுங்கள்.']}
            tamil_body='இந்தப் பாடத்தில் கவனித்தல், ஒப்பிடுதல், காரணம் கூறுதல் ஆகியவற்றைப் பயில்கிறோம். படத்தில் உள்ள விவரங்களைப் பார்த்து, உங்கள் பதிலுக்கான காரணத்தையும் விளக்குங்கள்.'
            # Subject-specific multilingual quizzes. Each lesson receives 3 questions with feedback.
            quiz_bank={
              'English':[
                ('Mia packed her bag, walked to school, then rang the bell. What happened second?','मीरा ने बैग रखा, स्कूल चली, फिर घंटी बजाई। दूसरी घटना कौन-सी थी?','மியா பையை எடுத்துக் கொண்டு பள்ளிக்குச் சென்றாள்; பின்னர் மணி அடித்தாள். இரண்டாவது நிகழ்வு எது?',['Packed her bag','Walked to school','Rang the bell','Went home'],['बैग रखा','स्कूल गई','घंटी बजाई','घर गई'],['பையை எடுத்தாள்','பள்ளிக்குச் சென்றாள்','மணி அடித்தாள்','வீட்டுக்குச் சென்றாள்'],1,'The events are in order: packed, walked, rang.','घटनाओं का क्रम है: बैग रखा, स्कूल गई, घंटी बजाई।','நிகழ்வுகளின் வரிசை: பையை எடுத்தாள், பள்ளிக்குச் சென்றாள், மணி அடித்தாள்।'),
                ('In “The tiny puppy curled beside its mother,” what does tiny mean?','“छोटा पिल्ला अपनी माँ के पास सिमट गया।” यहाँ “छोटा” का क्या अर्थ है?','“சிறிய நாய்க்குட்டி தன் அம்மாவின் அருகில் சுருண்டது.” இங்கே “சிறிய” என்பதன் பொருள் என்ன?',['Very small','Very noisy','Very hungry','Very fast'],['बहुत छोटा','बहुत शोर करने वाला','बहुत भूखा','बहुत तेज़'],['மிகச் சிறியது','மிகவும் சத்தமானது','மிகவும் பசித்தது','மிக வேகமானது'],0,'The word tiny describes size; it means very small.','“छोटा” आकार बताता है और इसका अर्थ बहुत छोटा है।','“சிறிய” என்பது அளவைக் குறிக்கிறது; மிகச் சிறியது என்பதே பொருள்.'),
                ('Which sentence is complete and punctuated correctly?','कौन-सा वाक्य पूरा है और उसमें विराम-चिह्न सही हैं?','எந்த வாக்கியம் முழுமையாகவும் சரியான நிறுத்தக்குறியுடனும் உள்ளது?',['Where is my book','My book is on the desk.','because I was late','the bright yellow sun'],['मेरी किताब कहाँ है','मेरी किताब मेज़ पर है।','क्योंकि मुझे देर हुई','चमकीला पीला सूरज'],['என் புத்தகம் எங்கே','என் புத்தகம் மேசையின் மேல் உள்ளது.','ஏனெனில் நான் தாமதமானேன்','பிரகாசமான மஞ்சள் சூரியன்'],1,'A complete sentence expresses a whole thought and ends with punctuation.','पूरा वाक्य संपूर्ण विचार बताता है और अंत में विराम-चिह्न होता है।','முழு வாக்கியம் முழுக் கருத்தைத் தெரிவித்து நிறுத்தக்குறியுடன் முடியும்.')],
              'Mathematics':[
                ('A number has {tens} tens and {ones} ones. What is the number?','एक संख्या में {tens} दहाइयाँ और {ones} इकाइयाँ हैं। संख्या क्या है?','ஒரு எண்ணில் {tens} பத்துகளும் {ones} ஒன்றுகளும் உள்ளன. அந்த எண் எது?',['{answer}','{reverse}','{plus}','{minus}'],['{answer}','{reverse}','{plus}','{minus}'],['{answer}','{reverse}','{plus}','{minus}'],0,'Tens give the tens-place value and ones give the ones-place value. Combine them to make the number.','दहाइयों का मान दहाई के स्थान पर और इकाइयों का मान इकाई के स्थान पर आता है।','பத்துகளின் மதிப்பு பத்துகள் இடத்திலும் ஒன்றுகளின் மதிப்பு ஒன்றுகள் இடத்திலும் வரும்.'),
                ('The pattern is 3, 5, 7, 9. Which rule predicts the next number?','श्रृंखला 3, 5, 7, 9 है। कौन-सा नियम अगली संख्या बताता है?','எண் வரிசை 3, 5, 7, 9. அடுத்த எண்ணைக் கணிக்க எந்த விதி உதவும்?',['Add 1 each time','Add 2 each time','Subtract 2 each time','Double each time'],['हर बार 1 जोड़ें','हर बार 2 जोड़ें','हर बार 2 घटाएँ','हर बार दोगुना करें'],['ஒவ்வொரு முறையும் 1 சேர்','ஒவ்வொரு முறையும் 2 சேர்','ஒவ்வொரு முறையும் 2 கழி','ஒவ்வொரு முறையும் இரட்டிப்பாக்கு'],1,'Each number increases by 2, so the rule is to add 2 each time.','हर अगली संख्या 2 बढ़ती है, इसलिए हर बार 2 जोड़ें।','ஒவ்வொரு அடுத்த எண்ணும் 2 அதிகரிக்கிறது; ஆகவே ஒவ்வொரு முறையும் 2 சேர்க்க வேண்டும்.'),
                ('A rectangle has 4 sides. Which description is always true?','एक आयत की 4 भुजाएँ होती हैं। कौन-सा कथन हमेशा सही है?','ஒரு செவ்வகத்திற்கு 4 பக்கங்கள் உள்ளன. எந்தக் கூற்று எப்போதும் சரி?',['All 4 sides must be equal','Opposite sides are equal','It has 3 corners','It has no straight sides'],['चारों भुजाएँ समान होவே चाहिए','विपरीत भुजाएँ बराबर होती हैं','इसके 3 कोने हैं','इसकी सीधी भुजाएँ नहीं हैं'],['நான்கு பக்கங்களும் சமமாக இருக்க வேண்டும்','எதிரெதிர் பக்கங்கள் சமம்','இதற்கு 3 மூலைகள் உள்ளன','இதற்கு நேரான பக்கங்கள் இல்லை'],1,'In a rectangle, opposite sides are equal and it has four right angles.','आयत की विपरीत भुजाएँ बराबर होती हैं और चार समकोण होते हैं।','செவ்வகத்தின் எதிரெதிர் பக்கங்கள் சமம்; நான்கு செங்கோணங்கள் உள்ளன.')],
              'Science':[
                ('Which plant part mainly takes in water from the soil?','पौधे का कौन-सा भाग मिट्टी से पानी लेता है?','மண்ணிலிருந்து நீரை முக்கியமாக உறிஞ்சும் தாவரப் பகுதி எது?',['Flower','Root','Fruit','Petal'],['फूल','जड़','फल','पंखुड़ी'],['மலர்','வேர்','பழம்','இதழ்'],1,'Roots absorb water and help hold the plant in the soil.','जड़ें पानी सोखती हैं और पौधे को मिट्टी में टिकाए रखती हैं।','வேர்கள் நீரை உறிஞ்சி தாவரத்தை மண்ணில் நிலைநிறுத்துகின்றன.'),
                ('To compare how much water two materials absorb, what makes the test fair?','दो पदार्थ कितना पानी सोखते हैं, इसकी निष्पक्ष जाँच कैसे होगी?','இரு பொருட்கள் எவ்வளவு நீரை உறிஞ்சுகின்றன என்பதை நியாயமாகச் சோதிப்பது எப்படி?',['Use equal-sized pieces and the same amount of water','Use a large piece for one and a tiny piece for the other','Pour different amounts of water','Change the time for every test'],['समान आकार के टुकड़े और समान पानी लें','एक बड़ा और एक बहुत छोटा टुकड़ा लें','अलग-अलग मात्रा में पानी डालें','हर जाँच का समय बदलें'],['ஒரே அளவுள்ள துண்டுகளுக்கும் ஒரே அளவு நீரையும் பயன்படுத்துங்கள்','ஒன்றுக்கு பெரியதும் மற்றொன்றுக்கு சிறியதுமான துண்டை எடுங்கள்','வெவ்வேறு அளவு நீர் ஊற்றுங்கள்','ஒவ்வொரு சோதனையிலும் நேரத்தை மாற்றுங்கள்'],0,'Keep the sample size and water amount the same so the material is the main variable.','नमूने का आकार और पानी की मात्रा समान रखें ताकि पदार्थ ही मुख्य बदला हुआ कारक हो।','மாதிரி அளவும் நீரின் அளவும் ஒன்றாக இருக்க வேண்டும்; அப்போது பொருளே முக்கிய மாறியாக இருக்கும்.'),
                ('When is a person’s outdoor shadow usually longer?','बाहर किसी व्यक्ति की छाया आम तौर पर कब लंबी होती है?','வெளியில் ஒருவரின் நிழல் பொதுவாக எப்போது நீளமாக இருக்கும்?',['When the Sun is low in the sky','Only at noon','When there is no light source','It never changes'],['जब सूर्य आकाश में नीचे होता है','केवल दोपहर में','जब प्रकाश का स्रोत नहीं होता','यह कभी नहीं बदलती'],['சூரியன் வானில் தாழ்வாக இருக்கும் போது','நண்பகலில் மட்டும்','ஒளி மூலமே இல்லாதபோது','அது ஒருபோதும் மாறாது'],0,'A low Sun angle usually creates a longer shadow; near noon the shadow is often shorter.','सूर्य नीचे होने पर छाया लंबी होती है; दोपहर के पास अक्सर छोटी होती है।','சூரியன் தாழ்வாக இருக்கும் போது நிழல் நீளமாகும்; நண்பகலில் பொதுவாகக் குறையும்.')],
              'Social Studies':[
                ('Who is trained to check and care for people’s teeth?','लोगों के दाँतों की जाँच और देखभाल कौन करता है?','மக்களின் பற்களைப் பரிசோதித்து பராமரிப்பவர் யார்?',['Farmer','Dentist','Map maker','Bus driver'],['किसान','दंत चिकित्सक','नक्शा बनाने वाला','बस चालक'],['விவசாயி','பல் மருத்துவர்','வரைபடம் வரைவவர்','பேருந்து ஓட்டுநர்'],1,'A dentist is trained to examine and care for teeth.','दंत चिकित्सक दाँतों की जाँच और देखभाल के लिए प्रशिक्षित होता है।','பல் மருத்துவர் பற்களைப் பரிசோதித்து பராமரிக்கப் பயிற்சி பெற்றவர்.'),
                ('What does a map key or legend help you understand?','नक्शे की कुंजी या संकेत-सूची किसमें मदद करती है?','வரைபடத்தின் குறியீட்டு விளக்கம் எதைப் புரிந்துகொள்ள உதவுகிறது?',['What symbols mean','Tomorrow’s weather','Every person’s name','The age of a building'],['संकेतों का अर्थ','कल का मौसम','हर व्यक्ति का नाम','इमारत की उम्र'],['குறியீடுகளின் பொருள்','நாளைய வானிலை','ஒவ்வொருவரின் பெயர்','கட்டிடத்தின் வயது'],0,'A map key explains what the symbols on a map represent.','नक्शे की कुंजी बताती है कि नक्शे के संकेत क्या दर्शाते हैं।','வரைபடத்தில் உள்ள குறியீடுகள் எதைக் குறிக்கின்றன என்பதை விளக்குகிறது.'),
                ('Which choice best protects a shared natural resource?','साझा प्राकृतिक संसाधन की रक्षा करने का सबसे अच्छा तरीका क्या है?','பொதுவான இயற்கை வளத்தைப் பாதுகாக்கும் சிறந்த செயல் எது?',['Leave taps running','Throw rubbish into a stream','Repair and reuse useful items','Cut trees for fun'],['नल खुला छोड़ दें','कचरा नदी में फेंकें','उपयोगी वस्तुओं की मरम्मत कर फिर उपयोग करें','मनोरंजन के लिए पेड़ काटें'],['குழாயைத் திறந்தே விடுங்கள்','குப்பையை ஓடையில் வீசுங்கள்','பயனுள்ள பொருட்களைச் சரிசெய்து மீண்டும் பயன்படுத்துங்கள்','வேடிக்கைக்காக மரங்களை வெட்டுங்கள்'],2,'Repairing and reusing items reduces waste and helps conserve resources.','वस्तुओं की मरम्मत और पुनः उपयोग से कचरा घटता है और संसाधन बचते हैं।','பொருட்களைச் சரிசெய்து மீண்டும் பயன்படுத்துவது கழிவைக் குறைத்து வளங்களைச் சேமிக்கிறது.')],
              'Tamil':[
                ('When you meet an unfamiliar Tamil word, what is a useful first step?','तमिल का अपरिचित शब्द मिलने पर पहला उपयोगी कदम क्या है?','புதிய தமிழ்ச் சொல்லைக் காணும்போது முதலில் செய்ய வேண்டிய பயனுள்ள செயல் எது?',['Read the surrounding sentence for clues','Guess without reading','Ignore the whole paragraph','Choose the longest word'],['आसपास का वाक्य पढ़कर संकेत खोजें','बिना पढ़े अनुमान लगाएँ','पूरा अनुच्छेद अनदेखा करें','सबसे लंबा शब्द चुनें'],['சுற்றியுள்ள வாக்கியத்தை வாசித்து குறிப்பைக் கண்டறியுங்கள்','வாசிக்காமல் ஊகியுங்கள்','முழுப் பத்தியையும் புறக்கணியுங்கள்','நீளமான சொல்லைத் தேர்ந்தெடுங்கள்'],0,'Context clues help you work out a word’s meaning in a sentence.','संदर्भ से वाक्य में शब्द का अर्थ समझने में मदद मिलती है।','சூழல் குறிப்புகள் வாக்கியத்தில் சொல்லின் பொருளைக் கண்டறிய உதவும்.'),
                ('Which order best describes a story?','कहानी का सबसे अच्छा क्रम कौन-सा है?','ஒரு கதையை விளக்கும் சிறந்த வரிசை எது?',['Ending, beginning, middle','Beginning, middle, ending','Middle, ending, beginning','Only the ending'],['अंत, शुरुआत, बीच','शुरुआत, बीच, अंत','बीच, अंत, शुरुआत','केवल अंत'],['முடிவு, தொடக்கம், நடுப்பு','தொடக்கம், நடுப்பு, முடிவு','நடுப்பு, முடிவு, தொடக்கம்','முடிவு மட்டும்'],1,'Stories are easier to understand when events are arranged from beginning to end.','घटनाओं को शुरुआत से अंत तक रखने पर कहानी समझना आसान होता है।','நிகழ்வுகளைத் தொடக்கம் முதல் முடிவு வரை வரிசைப்படுத்தினால் கதையைப் புரிந்துகொள்ளலாம்.'),
                ('Which action shows care for nature?','कौन-सा काम प्रकृति की देखभाल दिखाता है?','எந்தச் செயல் இயற்கையின் மீது அக்கறையைக் காட்டுகிறது?',['Waste clean water','Plant and care for a tree','Leave plastic on the ground','Pull flowers for no reason'],['साफ पानी बर्बाद करना','पेड़ लगाकर उसकी देखभाल करना','प्लास्टिक ज़मीन पर छोड़ना','बिना कारण फूल तोड़ना'],['சுத்தமான நீரை வீணாக்குதல்','மரம் நட்டு பராமரித்தல்','பிளாஸ்டிக்கை தரையில் விடுதல்','காரணமின்றி மலர்களைப் பறித்தல்'],1,'Planting and caring for trees helps living things and the environment.','पेड़ लगाना और उनकी देखभाल जीवों तथा पर्यावरण की मदद करता है।','மரம் நட்டு பராமரிப்பது உயிரினங்களுக்கும் சுற்றுச்சூழலுக்கும் உதவுகிறது.')]
            }
            math_question_template=quiz_bank['Mathematics'][0]
            for grade in range(1,6):
              # Make the number questions scale to the learner's assigned grade.
              tens=grade+1; ones=grade+3; answer=tens*10+ones
              reverse=ones*10+tens
              # Keep distractors plausible and distinct across grade levels.
              plus=answer+10; minus=answer-1
              quiz_bank['Mathematics'][0]=(
                math_question_template[0].format(tens=tens,ones=ones),
                math_question_template[1].format(tens=tens,ones=ones),
                math_question_template[2].format(tens=tens,ones=ones),
                [str(answer),str(reverse),str(plus),str(minus)],
                [str(answer),str(reverse),str(plus),str(minus)],
                [str(answer),str(reverse),str(plus),str(minus)],0,
                math_question_template[7],math_question_template[8],math_question_template[9])
              for subject in subjects:
                for j,(title,body) in enumerate(lesson_templates[subject]):
                  # keep exactly 75 grade/subject/lesson combinations
                  title_en=f'Grade {grade}: {title} {j+1}'
                  title_hi=f'कक्षा {grade}: {titles_hi[subject][j]}'
                  title_ta=f'{grade}ஆம் வகுப்பு: {titles_ta[subject][j]}'
                  body_en=f'{body} Grade {grade} challenge: use the picture clue, explain your reasoning, and check whether another example follows the same rule.'
                  body_hi=f'इस पाठ में हम ध्यान से देखना, तुलना करना और कारण बताना सीखते हैं। चित्र में दिए संकेतों को देखें, उत्तर चुनें और अपने उत्तर का कारण समझाएँ। कक्षा {grade} चुनौती: अपने विचार को एक उदाहरण से जाँचें।'
                  body_ta=tamil_body+f' {grade}ஆம் வகுப்பு சவால்: படத்தில் உள்ள குறிப்புகளைப் பயன்படுத்தி உங்கள் காரணத்தை விளக்குங்கள்.'
                  picture={'English':['📚','🔤','✍️'],'Mathematics':['🔢','🧩','🔺'],'Science':['🌱','🧪','🌦️'],'Social Studies':['🏘️','🗺️','🌍'],'Tamil':['🔠','📖','🌳']}[subject][j]
                  grade_detail_en={1:'Point to the picture, name the important object and say one thing you notice.',2:'Compare two examples and explain one similarity and one difference.',3:'Sort the examples, find a rule and give a reason for your choice.',4:'Use two clues to solve the task and explain why another answer does not fit.',5:'Apply the idea to a new situation and support your conclusion with evidence.'}[grade]
                  grade_detail_hi={1:'चित्र में वस्तु पहचानें, उसका नाम बोलें और एक बात बताएँ।',2:'दो उदाहरणों की तुलना करके एक समानता और एक अंतर बताएँ।',3:'उदाहरणों को समूहों में रखें, नियम पहचानें और कारण बताएँ।',4:'दो संकेतों से समस्या हल करें और समझाएँ कि दूसरा उत्तर क्यों नहीं है।',5:'सीखी हुई बात को नई स्थिति में लागू करके प्रमाण के साथ निष्कर्ष बताएँ।'}[grade]
                  grade_detail_ta={1:'படத்தில் உள்ள பொருளைக் கண்டுபிடித்து ஒரு குறிப்பைக் கூறுங்கள்.',2:'இரண்டு எடுத்துக்காட்டுகளை ஒப்பிட்டு ஒரு ஒற்றுமையும் வேறுபாடும் கூறுங்கள்.',3:'எடுத்துக்காட்டுகளை வகைப்படுத்தி விதியைக் கண்டறிந்து காரணம் கூறுங்கள்.',4:'இரண்டு குறிப்புகளைப் பயன்படுத்தித் தீர்த்து மற்ற பதில் ஏன் பொருந்தாது என விளக்குங்கள்.',5:'கற்ற கருத்தை புதிய சூழலில் பயன்படுத்தி ஆதாரத்துடன் முடிவை விளக்குங்கள்.'}[grade]
                  body_en=f'{body} Grade {grade} challenge: {grade_detail_en}'
                  body_hi=f'{body_hi_map[subject][j]} कक्षा {grade} गतिविधि: {grade_detail_hi}'
                  body_ta=f'{body_ta_map[subject][j]} {grade}ஆம் வகுப்பு செயல்: {grade_detail_ta}'
                  cur=c.execute('INSERT INTO lessons(title_en,title_hi,subject,grade,body_en,body_hi,published,created_by,title_ta,body_ta,picture) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(title_en,title_hi,subject,grade,body_en,body_hi,1,teacher,title_ta,body_ta,picture))
                  lid=cur.lastrowid
                  # Three reasoning-oriented questions per lesson, options deliberately include plausible distractors.
                  qs=quiz_bank[subject]
                  for k,q in enumerate(qs):
                    c.execute('INSERT INTO questions(lesson_id,prompt_en,prompt_hi,options_en,options_hi,correct_index,explanation_en,explanation_hi,prompt_ta,options_ta,explanation_ta) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(lid,q[0],q[1],json.dumps(q[3],ensure_ascii=False),json.dumps(q[4],ensure_ascii=False),q[6],q[7],q[8],q[2],json.dumps(q[5],ensure_ascii=False),q[9]))
        # Grade-specific teacher accounts, 3 sections per grade and 20 students per section.
        # These are sample identities for the local prototype. Attendance is sample data, not live school records.
        first_names=['Aarav','Ananya','Arjun','Diya','Ishaan','Kavya','Vihaan','Meera','Aditya','Nila','Rohan','Aadhya','Kiran','Priya','Sanjay','Mithra','Dev','Ira','Vikram','Janani']
        last_names=['Kumar','Ravi','Sharma','Devi','Raj','Nair','Das','Iyer','Singh','Priya','Murugan','Patel','Krishnan','Reddy','Bose','Menon','Gupta','Shah','Thomas','Selvan']
        section_names=['A','B','C']
        teacher_ids={}
        teacher_demo_hash=password_hash('Teach@123')
        student_demo_hash=password_hash('Learn@123')
        parent_demo_hash=password_hash('Parent@123')
        today=date.today()
        school_days=[]
        cursor=today
        while len(school_days)<5:
            if cursor.weekday()<5: school_days.append(cursor)
            cursor-=timedelta(days=1)
        school_days=list(reversed(school_days))
        for g in range(1,6):
            teacher_email=f'teacher.g{g}@udaan.local'
            row=c.execute('SELECT id FROM users WHERE lower(email)=lower(?)',(teacher_email,)).fetchone()
            if not row:
                c.execute('INSERT INTO users(name,email,role,password_hash,grade) VALUES(?,?,?,?,?)',(f'Grade {g} Teacher',teacher_email,'teacher',teacher_demo_hash,g))
                row=c.execute('SELECT id FROM users WHERE lower(email)=lower(?)',(teacher_email,)).fetchone()
            else:
                c.execute('UPDATE users SET name=?,grade=? WHERE id=?',(f'Grade {g} Teacher',g,row['id']))
            teacher_ids[g]=row['id']
            for section_index,section in enumerate(section_names):
                for roll in range(1,21):
                    key=f'g{g}{section.lower()}{roll:02d}'
                    student_email=f'student.{key}@udaan.local'
                    parent_email=f'parent.{key}@udaan.local'
                    given=first_names[(roll-1+g*2+section_index*5)%len(first_names)]
                    family=last_names[(roll-1+g+section_index*4)%len(last_names)]
                    full_name=f'{given} {family}'
                    roll_label=f'G{g}-{section}{roll:02d}'
                    sr=c.execute('SELECT id FROM users WHERE lower(email)=lower(?)',(student_email,)).fetchone()
                    if not sr:
                        c.execute('INSERT INTO users(name,email,role,password_hash,grade,class_name,roll_number) VALUES(?,?,?,?,?,?,?)',(full_name,student_email,'student',student_demo_hash,g,section,roll_label))
                        sid=c.execute('SELECT id FROM users WHERE lower(email)=lower(?)',(student_email,)).fetchone()['id']
                    else:
                        sid=sr['id']
                        c.execute('UPDATE users SET name=?,grade=?,class_name=?,roll_number=? WHERE id=?',(full_name,g,section,roll_label,sid))
                    pr=c.execute('SELECT id FROM users WHERE lower(email)=lower(?)',(parent_email,)).fetchone()
                    if not pr:
                        c.execute('INSERT INTO users(name,email,role,password_hash,student_id,grade,class_name,roll_number) VALUES(?,?,?,?,?,?,?,?)',(f'Parent of {full_name}',parent_email,'parent',parent_demo_hash,sid,g,section,roll_label))
                    else:
                        c.execute('UPDATE users SET student_id=?,name=?,grade=?,class_name=?,roll_number=? WHERE id=?',(sid,f'Parent of {full_name}',g,section,roll_label,pr['id']))
                    for day_index,school_day in enumerate(school_days):
                        # Stable demo attendance pattern, with most records marked present.
                        value=(g*7+section_index*3+roll+day_index*5)%11
                        status='Absent' if value in (0,4) else 'Present'
                        c.execute('INSERT OR IGNORE INTO attendance(student_id,attendance_date,status) VALUES(?,?,?)',(sid,school_day.isoformat(),status))

init_db()
class LoginBody(BaseModel): email:str; password:str
class LessonBody(BaseModel): title_en:str; title_hi:str; title_ta:str=''; subject:str; grade:int=Field(ge=1,le=5); body_en:str; body_hi:str=''; body_ta:str=''; picture:str='🌈'; published:bool=True; visuals:list[dict]=Field(default_factory=list)
class QuestionBody(BaseModel): lesson_id:int; prompt_en:str; prompt_hi:str; prompt_ta:str=''; options_en:list[str]; options_hi:list[str]; options_ta:list[str]=[]; correct_index:int; explanation_en:str; explanation_hi:str; explanation_ta:str=''
class AttemptBody(BaseModel): lesson_id:int; answers:list[int]
class AssignmentBody(BaseModel): lesson_id:int; student_id:Optional[int]=None; class_name:Optional[str]=None; due_date:str=''; note:str=''
class ImportContentBody(BaseModel): filename:str='Uploaded material'; text:str; mode:str='new'; lesson_id:Optional[int]=None; subject:str='Science'; grade:int=Field(ge=1,le=5); title_en:str=''
class GenerateQuizBody(BaseModel): lesson_id:int; count:int=Field(default=5,ge=3,le=10)
class RewardActivityBody(BaseModel): activity:str; lesson_id:int
class AvatarBody(BaseModel): avatar_id:str
def current_user(authorization:Optional[str]):
    if not authorization or not authorization.startswith('Bearer '): raise HTTPException(401,'Please sign in to continue.')
    u=SESSIONS.get(authorization.split(' ',1)[1])
    if not u: raise HTTPException(401,'Session expired. Please sign in again.')
    return u
def teacher(u):
    if u['role']!='teacher':raise HTTPException(403,'Teacher access is required.')
def rowdict(r):return {k:r[k] for k in r.keys()}
AVATARS={
    'astro':{'name':'Captain Udaan','emoji':'🧑‍🚀','required':0},
    'fox':{'name':'Rocket Fox','emoji':'🦊','required':25},
    'panda':{'name':'Panda Pilot','emoji':'🐼','required':60},
    'unicorn':{'name':'Star Unicorn','emoji':'🦄','required':100},
    'dragon':{'name':'Galaxy Dragon','emoji':'🐉','required':180},
    'cat':{'name':'Cosmic Cat','emoji':'🐱','required':300},
}
def lesson_payload(r,c=None):
    d=rowdict(r)
    try:d['visuals']=json.loads(d.pop('visuals_json', '[]') or '[]')
    except Exception:d['visuals']=[]
    if c is not None:d['question_count']=c.execute('SELECT COUNT(*) FROM questions WHERE lesson_id=?',(r['id'],)).fetchone()[0]
    return d
def local_ollama(prompt,timeout=90,json_mode=False):
    model=os.getenv('OLLAMA_MODEL','qwen2.5:3b')
    payload={'model':model,'prompt':prompt,'stream':False}
    if json_mode:payload['format']='json'
    req=urllib.request.Request('http://127.0.0.1:11434/api/generate',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout) as res:
        return json.loads(res.read()).get('response','').strip()
def parse_json_object(text):
    clean=re.sub(r'^\s*```(?:json)?|```\s*$', '', text.strip(), flags=re.I|re.M).strip()
    start=clean.find('{'); end=clean.rfind('}')
    if start<0 or end<start:raise ValueError('AI did not return a JSON object')
    return json.loads(clean[start:end+1])
def default_visuals(subject,title,text):
    if subject=='Mathematics':items=[('🧩','Spot the pattern','Look for what changes and what stays the same.'),('🔢','Number explorer','Count, compare, and explain your thinking.'),('📐','Shape studio','Notice sides, corners, and shape clues.'),('🌟','Try it yourself','Solve one small challenge step by step.')]
    elif subject=='Science':items=[('🔍','Look closely','Observe the details before making a guess.'),('🌱','Nature detective','Connect the idea to plants, animals, or our planet.'),('🧪','Mini experiment','Ask a question and look for evidence.'),('🌎','Real-world link','Find where this idea appears around you.')]
    elif subject=='English':items=[('📖','Story world','Meet the idea, characters, and key details.'),('🦊','Word explorer','Use clues around a word to understand it.'),('💬','Say it aloud','Read a sentence and share what it means.'),('✏️','Create a sentence','Show what you learned in your own words.')]
    elif subject=='Tamil':items=[('🌺','சொல் உலகம்','சொற்களின் பொருளைக் கவனிப்போம்.'),('📚','கதை நேரம்','நிகழ்வுகளை வரிசையாகப் பார்ப்போம்.'),('🗣️','சொல்லிப் பார்ப்போம்','புதிய சொல்லை தெளிவாகச் சொல்வோம்.'),('🌿','சுற்றி கவனி','பாடத்தை நம் உலகத்துடன் இணைப்போம்.')]
    else:items=[('🗺️','Explore the place','Notice people, places, and connections.'),('🏘️','Community clues','Find how people help one another.'),('🕰️','Then and now','Compare what changed and what stayed.'),('🌍','Our shared world','Connect the lesson to everyday life.')]
    short=re.sub(r'\s+',' ',title).strip()[:70] or 'Today’s discovery'
    return [{'emoji':e,'title':t,'caption':(f'{c} Topic: {short}.')[:180]} for e,t,c in items]
def tidy_for_children(text,grade):
    lines=[]
    for raw in text.replace('\r','').split('\n'):
        line=re.sub(r'\s+',' ',raw).strip()
        if not line or re.fullmatch(r'\d+',line) or re.fullmatch(r'page\s+\d+',line,re.I):continue
        lines.append(line)
    merged='\n'.join(lines);merged=re.sub(r'\n{3,}','\n\n',merged).strip()
    sentences=re.split(r'(?<=[.!?])\s+',merged);chunks=[];current=[];limit=2 if grade<=2 else 3
    for sentence in sentences:
        if sentence.strip():current.append(sentence.strip())
        if len(current)>=limit:chunks.append(' '.join(current));current=[]
    if current:chunks.append(' '.join(current))
    return '\n\n'.join(chunks)[:12000]
@app.get('/', include_in_schema=False)
def root():
    index=FRONTEND_DIR/'index.html'
    if index.is_file():return FileResponse(index)
    return {'name':'Udaan Primary Learning API','status':'ok','docs':'/docs'}
@app.get('/api/health')
def health():return {'status':'ok','service':'udaan-api'}
@app.post('/api/login')
def login(b:LoginBody):
    with db() as c:r=c.execute('SELECT * FROM users WHERE lower(email)=lower(?)',(b.email.strip(),)).fetchone()
    if not r or not password_matches(b.password,r['password_hash']):raise HTTPException(401,'Email or password is incorrect.')
    u={'id':r['id'],'name':r['name'],'email':r['email'],'role':r['role'],'grade':r['grade'],'student_id':r['student_id'],'class_name':r['class_name'],'roll_number':r['roll_number'],'stars':r['stars'],'avatar':r['avatar']}; t=secrets.token_urlsafe(32);SESSIONS[t]=u;return {'token':t,'user':u}
@app.get('/api/me')
def me(authorization:Optional[str]=Header(default=None)):return current_user(authorization)
@app.post('/api/logout')
def logout(authorization:Optional[str]=Header(default=None)):
    if authorization and authorization.startswith('Bearer '):SESSIONS.pop(authorization.split(' ',1)[1],None)
    return {'ok':True}
@app.get('/api/students')
def students(authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization);teacher(u)
    with db() as c:
        grade_filter=u.get('grade')
        rows=c.execute("SELECT id,name,email,grade,class_name,roll_number FROM users WHERE role='student' AND class_name<>'' AND (? IS NULL OR grade=?) ORDER BY grade,class_name,roll_number",(grade_filter,grade_filter)).fetchall()
        return [dict(r) for r in rows]
@app.get('/api/lessons')
def lessons(grade:Optional[int]=None,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization)
    with db() as c:
        if u['role']=='teacher':
            g=u.get('grade')
            rows=c.execute('SELECT * FROM lessons WHERE (? IS NULL OR grade=?) ORDER BY grade,subject,id',(g,g)).fetchall()
        else:
            # A learner or parent cannot switch the account to another grade by changing a URL parameter.
            if u['role']=='student':g=u.get('grade')
            elif u['role']=='parent' and u.get('student_id'):
                linked=c.execute('SELECT grade FROM users WHERE id=?',(u['student_id'],)).fetchone();g=linked['grade'] if linked else None
            else:g=None
            rows=c.execute('SELECT * FROM lessons WHERE published=1 AND (? IS NULL OR grade=?) ORDER BY subject,id',(g,g)).fetchall()
        out=[]
        for r in rows:
            d=lesson_payload(r,c);out.append(d)
        return out
@app.post('/api/lessons')
def create_lesson(b:LessonBody,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization);teacher(u)
    if u.get('grade') and b.grade!=u.get('grade'): raise HTTPException(403,'This teacher account is assigned to a different grade.')
    with db() as c:
        cur=c.execute('INSERT INTO lessons(title_en,title_hi,subject,grade,body_en,body_hi,published,created_by,title_ta,body_ta,picture,visuals_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(b.title_en,b.title_hi,b.subject,b.grade,b.body_en,b.body_hi,int(b.published),u['id'],b.title_ta,b.body_ta,b.picture,json.dumps(b.visuals or [],ensure_ascii=False)));return lesson_payload(c.execute('SELECT * FROM lessons WHERE id=?',(cur.lastrowid,)).fetchone(),c)
@app.put('/api/lessons/{lid}')
def update_lesson(lid:int,b:LessonBody,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization);teacher(u)
    if u.get('grade') and b.grade!=u.get('grade'): raise HTTPException(403,'This teacher account is assigned to a different grade.')
    with db() as c:
        cur=c.execute('UPDATE lessons SET title_en=?,title_hi=?,title_ta=?,subject=?,grade=?,body_en=?,body_hi=?,body_ta=?,picture=?,published=?,visuals_json=? WHERE id=?',(b.title_en,b.title_hi,b.title_ta,b.subject,b.grade,b.body_en,b.body_hi,b.body_ta,b.picture,int(b.published),json.dumps(b.visuals or [],ensure_ascii=False),lid))
        if not cur.rowcount:raise HTTPException(404,'Lesson not found')
        return lesson_payload(c.execute('SELECT * FROM lessons WHERE id=?',(lid,)).fetchone(),c)
@app.delete('/api/lessons/{lid}')
def delete_lesson(lid:int,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization);teacher(u)
    with db() as c:c.execute('DELETE FROM lessons WHERE id=?',(lid,));return {'ok':True}
@app.get('/api/lessons/{lid}/questions')
def questions(lid:int,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization)
    with db() as c:
        lesson=c.execute('SELECT grade,published FROM lessons WHERE id=?',(lid,)).fetchone()
        if not lesson or (u['role']!='teacher' and not lesson['published']):raise HTTPException(404,'Lesson not found.')
        if u['role']=='student' and lesson['grade']!=u.get('grade'):raise HTTPException(403,'This lesson is outside your assigned grade portal.')
        rows=c.execute('SELECT * FROM questions WHERE lesson_id=? ORDER BY id',(lid,)).fetchall()
    return [{'id':r['id'],'lesson_id':r['lesson_id'],'prompt_en':r['prompt_en'],'prompt_hi':r['prompt_hi'],'prompt_ta':r['prompt_ta'],'options_en':json.loads(r['options_en']),'options_hi':json.loads(r['options_hi']),'options_ta':json.loads(r['options_ta'] or '[]'),'explanation_en':r['explanation_en'],'explanation_hi':r['explanation_hi'],'explanation_ta':r['explanation_ta'],'correct_index':r['correct_index']} for r in rows]
@app.post('/api/questions')
def create_question(b:QuestionBody,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization);teacher(u)
    if len(b.options_en)<2 or len(b.options_en)>6 or len(b.options_en)!=len(b.options_hi) or len(b.options_en)!=len(b.options_ta or b.options_en) or b.correct_index<0 or b.correct_index>=len(b.options_en):raise HTTPException(422,'Provide 2–6 matching options in each language and a valid correct answer index.')
    with db() as c:
        lesson=c.execute('SELECT grade FROM lessons WHERE id=?',(b.lesson_id,)).fetchone()
        if not lesson:raise HTTPException(404,'Lesson not found.')
        if u.get('grade') and lesson['grade']!=u.get('grade'):raise HTTPException(403,'You can create quizzes only for your assigned grade.')
        cur=c.execute('INSERT INTO questions(lesson_id,prompt_en,prompt_hi,options_en,options_hi,correct_index,explanation_en,explanation_hi,prompt_ta,options_ta,explanation_ta) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(b.lesson_id,b.prompt_en,b.prompt_hi,json.dumps(b.options_en,ensure_ascii=False),json.dumps(b.options_hi,ensure_ascii=False),b.correct_index,b.explanation_en,b.explanation_hi,b.prompt_ta,json.dumps(b.options_ta or b.options_en,ensure_ascii=False),b.explanation_ta));return {'id':cur.lastrowid,'ok':True}
@app.post('/api/attempts')
def attempt(b:AttemptBody,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization)
    if u['role']!='student':raise HTTPException(403,'Student account required.')
    with db() as c:
        lesson=c.execute('SELECT grade,published FROM lessons WHERE id=?',(b.lesson_id,)).fetchone()
        if not lesson or not lesson['published']:raise HTTPException(404,'Lesson not found.')
        if lesson['grade']!=u.get('grade'):raise HTTPException(403,'You can only submit quizzes for your assigned grade.')
        qs=c.execute('SELECT id,correct_index FROM questions WHERE lesson_id=? ORDER BY id',(b.lesson_id,)).fetchall()
        if not qs:raise HTTPException(400,'This lesson has no quiz yet.')
        if len(b.answers)!=len(qs):raise HTTPException(422,'Please answer every question.')
        score=sum(1 for i,q in enumerate(qs) if b.answers[i]==q['correct_index']);cur=c.execute('INSERT INTO attempts(user_id,lesson_id,score,total,answers) VALUES(?,?,?,?,?)',(u['id'],b.lesson_id,score,len(qs),json.dumps(b.answers)))
        reward_day=date.today().isoformat();reward_key=f'quiz:{b.lesson_id}';base_stars=10+(5 if score==len(qs) else 0)
        reward_cur=c.execute('INSERT OR IGNORE INTO reward_events(user_id,activity_key,event_day,stars) VALUES(?,?,?,?)',(u['id'],reward_key,reward_day,base_stars))
        reward_awarded=0
        if reward_cur.rowcount:
            reward_awarded+=base_stars;c.execute('UPDATE users SET stars=stars+? WHERE id=?',(base_stars,u['id']))
        assigned=c.execute('SELECT id FROM assignments WHERE student_id=? AND lesson_id=?',(u['id'],b.lesson_id)).fetchall()
        for ar in assigned:
            key=f'assignment-complete:{ar[0]}'
            ac=c.execute('INSERT OR IGNORE INTO reward_events(user_id,activity_key,event_day,stars) VALUES(?,?,?,?)',(u['id'],key,'once',5))
            if ac.rowcount:reward_awarded+=5;c.execute('UPDATE users SET stars=stars+5 WHERE id=?',(u['id'],))
        total_stars=c.execute('SELECT stars FROM users WHERE id=?',(u['id'],)).fetchone()['stars']
        return {'id':cur.lastrowid,'score':score,'total':len(qs),'percentage':round(score/len(qs)*100),'correct_indices':[q['correct_index'] for q in qs],'reward_awarded':reward_awarded,'star_points':total_stars}
@app.get('/api/progress')
def progress(authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization)
    if u['role']!='student':raise HTTPException(403,'Student account required.')
    with db() as c:
        rows=c.execute('SELECT a.*,l.title_en,l.title_hi,l.title_ta FROM attempts a JOIN lessons l ON l.id=a.lesson_id WHERE a.user_id=? ORDER BY a.created_at DESC',(u['id'],)).fetchall();total=c.execute('SELECT COUNT(*) FROM lessons WHERE published=1 AND grade=?',(u.get('grade') or 3,)).fetchone()[0]
        day_rows=[r['day'] for r in c.execute('SELECT DISTINCT date(created_at) day FROM attempts WHERE user_id=? ORDER BY day DESC',(u['id'],)).fetchall()]
        day_set=set(day_rows);streak=0;d=date.today()
        if d.isoformat() not in day_set: d-=timedelta(days=1)
        while d.isoformat() in day_set: streak+=1;d-=timedelta(days=1)
        attendance_rows=c.execute('SELECT attendance_date,status FROM attendance WHERE student_id=? ORDER BY attendance_date DESC LIMIT 5',(u['id'],)).fetchall()
        return {'attempts':[dict(id=r['id'],lesson_id=r['lesson_id'],title_en=r['title_en'],title_hi=r['title_hi'],title_ta=r['title_ta'],score=r['score'],total=r['total'],created_at=r['created_at'],percentage=round(r['score']/r['total']*100) if r['total'] else 0) for r in rows],'completed_lessons':len(set(r['lesson_id'] for r in rows)),'available_lessons':total,'attempt_count':len(rows),'average_percentage':round(sum(r['score']/r['total']*100 for r in rows)/len(rows)) if rows else 0,'streak_days':streak,'weekly_attempts':sum(1 for r in rows if r['created_at'][:10]>=(date.today()-timedelta(days=6)).isoformat()),'attendance_week':[dict(date=r['attendance_date'],status=r['status']) for r in attendance_rows],'class_name':u.get('class_name',''),'roll_number':u.get('roll_number',''),'star_points':c.execute('SELECT stars FROM users WHERE id=?',(u['id'],)).fetchone()['stars'],'avatar_id':c.execute('SELECT avatar FROM users WHERE id=?',(u['id'],)).fetchone()['avatar'],'avatars':[dict(id=k,**v,unlocked=c.execute('SELECT stars FROM users WHERE id=?',(u['id'],)).fetchone()['stars']>=v['required']) for k,v in AVATARS.items()]}
@app.post('/api/assignments')
def assign(b:AssignmentBody,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization);teacher(u)
    with db() as c:
        lesson=c.execute('SELECT grade FROM lessons WHERE id=?',(b.lesson_id,)).fetchone()
        if not lesson: raise HTTPException(404,'Lesson not found.')
        if u.get('grade') and lesson['grade']!=u.get('grade'): raise HTTPException(403,'This teacher can assign work only within their grade.')
        # Assign by class section: create one assignment per learner in that section.
        if b.class_name:
            if b.class_name not in ('A','B','C'): raise HTTPException(422,'Choose class A, B or C.')
            if not u.get('grade'): raise HTTPException(403,'Use a grade-specific teacher account to assign classwork.')
            if lesson['grade'] != u['grade']: raise HTTPException(422,'Choose a lesson for your grade.')
            learners=c.execute("SELECT id FROM users WHERE role='student' AND grade=? AND class_name=? ORDER BY roll_number",(u['grade'],b.class_name)).fetchall()
            if not learners: raise HTTPException(404,'No students found in this class section.')
            c.executemany('INSERT INTO assignments(lesson_id,student_id,teacher_id,due_date,note) VALUES(?,?,?,?,?)',[(b.lesson_id,r['id'],u['id'],b.due_date,b.note) for r in learners])
            return {'ok':True,'assigned_count':len(learners),'class_name':b.class_name,'grade':u['grade']}
        if not b.student_id: raise HTTPException(422,'Choose a class section to assign this lesson.')
        student=c.execute("SELECT grade,class_name FROM users WHERE id=? AND role='student'",(b.student_id,)).fetchone()
        if not student:raise HTTPException(404,'Student not found.')
        if lesson['grade']!=student['grade']:raise HTTPException(422,'Choose a lesson from the same grade as the student.')
        cur=c.execute('INSERT INTO assignments(lesson_id,student_id,teacher_id,due_date,note) VALUES(?,?,?,?,?)',(b.lesson_id,b.student_id,u['id'],b.due_date,b.note));return {'id':cur.lastrowid,'ok':True,'assigned_count':1}
@app.get('/api/assignments')
def get_assignments(authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization)
    with db() as c:
        if u['role']=='teacher':
            rows=c.execute('SELECT a.*,l.title_en,l.title_hi,l.title_ta,s.name student_name,s.grade,s.email,s.class_name,s.roll_number FROM assignments a JOIN lessons l ON l.id=a.lesson_id JOIN users s ON s.id=a.student_id WHERE (? IS NULL OR s.grade=?) ORDER BY a.created_at DESC',(u.get('grade'),u.get('grade'))).fetchall()
        else:
            sid=u['id'] if u['role']=='student' else u.get('student_id')
            rows=c.execute('SELECT a.*,l.title_en,l.title_hi,l.title_ta,s.name student_name,s.grade,s.email FROM assignments a JOIN lessons l ON l.id=a.lesson_id JOIN users s ON s.id=a.student_id WHERE a.student_id=? ORDER BY a.created_at DESC',(sid,)).fetchall() if sid else []
        out=[]
        for r in rows:
            d=rowdict(r);a=c.execute('SELECT score,total,created_at FROM attempts WHERE user_id=? AND lesson_id=? ORDER BY created_at DESC LIMIT 1',(r['student_id'],r['lesson_id'])).fetchone();d['status']='Completed' if a else 'Pending';d['score']=a['score'] if a else None;d['total']=a['total'] if a else None;out.append(d)
        return out
@app.get('/api/parent/overview')
def parent_overview(authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization)
    if u['role']!='parent':raise HTTPException(403,'Parent account required.')
    sid=u.get('student_id')
    if not sid:raise HTTPException(404,'No student linked to this parent demo account.')
    with db() as c:
        s=c.execute('SELECT id,name,grade,email,class_name,roll_number FROM users WHERE id=?',(sid,)).fetchone();attendance=c.execute('SELECT attendance_date,status FROM attendance WHERE student_id=? ORDER BY attendance_date DESC LIMIT 5',(sid,)).fetchall();attendance=list(reversed(attendance));attempts=c.execute('SELECT a.*,l.title_en,l.title_hi,l.title_ta FROM attempts a JOIN lessons l ON l.id=a.lesson_id WHERE a.user_id=? ORDER BY a.created_at DESC',(sid,)).fetchall();assignments=c.execute('SELECT a.*,l.title_en FROM assignments a JOIN lessons l ON l.id=a.lesson_id WHERE a.student_id=? ORDER BY a.created_at DESC',(sid,)).fetchall()
        return {'student':dict(s),'attempts':[dict(r) for r in attempts],'assignments':[dict(r) for r in assignments],'average_percentage':round(sum(r['score']/r['total']*100 for r in attempts)/len(attempts)) if attempts else 0,'completed_lessons':len(set(r['lesson_id'] for r in attempts)),'weekly_attempts':sum(1 for r in attempts if r['created_at'][:10]>=(date.today()-timedelta(days=6)).isoformat()),'attendance_week':[dict(date=r['attendance_date'],status=r['status']) for r in attendance]}
@app.get('/api/teacher/progress')
def teacher_progress(class_name:str='A',authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization);teacher(u)
    if class_name not in ('A','B','C'): raise HTTPException(422,'Choose class A, B or C.')
    grade=u.get('grade')
    if not grade: raise HTTPException(403,'Use a grade-specific teacher account to view a class report.')
    with db() as c:
        students=c.execute("SELECT id,name,grade,class_name,roll_number FROM users WHERE role='student' AND grade=? AND class_name=? ORDER BY roll_number",(grade,class_name)).fetchall()
        today=date.today();days=[];cursor=today
        while len(days)<5:
            if cursor.weekday()<5:days.append(cursor.isoformat())
            cursor-=timedelta(days=1)
        days=list(reversed(days))
        out=[]
        for student in students:
            att_rows=c.execute('SELECT attendance_date,status FROM attendance WHERE student_id=? AND attendance_date IN (?,?,?,?,?)',(student['id'],*days)).fetchall()
            att={r['attendance_date']:r['status'] for r in att_rows}
            attempts=c.execute("SELECT score,total,created_at,lesson_id FROM attempts WHERE user_id=? AND date(created_at)>=date('now','-6 days') ORDER BY created_at DESC",(student['id'],)).fetchall()
            avg=round(sum((r['score']/r['total']*100) for r in attempts)/len(attempts)) if attempts else 0
            completed=len(set(r['lesson_id'] for r in attempts))
            out.append({'id':student['id'],'name':student['name'],'grade':student['grade'],'class_name':student['class_name'],'roll_number':student['roll_number'],'attendance':[{ 'date':d,'status':att.get(d,'—')} for d in days],'attendance_percent':round(sum(1 for d in days if att.get(d)=='Present')/5*100),'weekly_quizzes':len(attempts),'weekly_average':avg,'weekly_lessons_completed':completed})
        return {'grade':grade,'class_name':class_name,'week_days':days,'students':out,'attendance_sample':True}

@app.post('/api/generate-quiz')
def generate_quiz(b:GenerateQuizBody,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization);teacher(u)
    with db() as c:
        lesson=c.execute('SELECT * FROM lessons WHERE id=?',(b.lesson_id,)).fetchone()
        if not lesson:raise HTTPException(404,'Choose a lesson first.')
        if u.get('grade') and lesson['grade']!=u.get('grade'):raise HTTPException(403,'This teacher account is assigned to a different grade.')
        prompt=f'''Create exactly {b.count} age-appropriate multiple-choice quiz questions for Grade {lesson['grade']} students.
Subject: {lesson['subject']}. Lesson title: {lesson['title_en']}.
Lesson content (use only these facts):
{lesson['body_en'][:9000]}
Return a JSON object with key "questions" containing exactly {b.count} items. Every item must have:
prompt_en, prompt_hi, prompt_ta, options_en (4 strings), options_hi (4 strings), options_ta (4 strings), correct_index (integer 0-3), explanation_en, explanation_hi, explanation_ta.
Make distractors plausible but fair, avoid trick questions, use child-friendly language, and ensure one correct answer. Return JSON only.'''
        try:
            output=local_ollama(prompt,timeout=120,json_mode=True);parsed=parse_json_object(output);items=parsed.get('questions',[])
            if not isinstance(items,list) or len(items)<b.count:raise ValueError(f'AI returned fewer than the requested {b.count} questions')
            # Validate the entire draft before writing anything. A malformed AI response must not leave a partial quiz in the database.
            validated=[]
            for item in items[:b.count]:
                if not isinstance(item,dict):raise ValueError('AI returned a malformed question')
                opts=item.get('options_en') or []
                if not isinstance(opts,list) or len(opts)!=4 or any(not str(x).strip() for x in opts):raise ValueError('AI question must contain four non-empty English options')
                correct=int(item.get('correct_index',-1))
                if correct<0 or correct>=len(opts):raise ValueError('AI question has an invalid correct answer')
                opts_hi=item.get('options_hi') or opts;opts_ta=item.get('options_ta') or opts
                if not isinstance(opts_hi,list) or len(opts_hi)!=4:opts_hi=opts
                if not isinstance(opts_ta,list) or len(opts_ta)!=4:opts_ta=opts
                prompt_en=str(item.get('prompt_en') or '').strip()
                if not prompt_en:raise ValueError('AI returned a question without text')
                validated.append((prompt_en,str(item.get('prompt_hi') or prompt_en),str(item.get('prompt_ta') or prompt_en),opts,opts_hi,opts_ta,correct,str(item.get('explanation_en') or ''),str(item.get('explanation_hi') or item.get('explanation_en') or ''),str(item.get('explanation_ta') or item.get('explanation_en') or '')))
            created=[]
            for prompt_en,prompt_hi,prompt_ta,opts,opts_hi,opts_ta,correct,exp_en,exp_hi,exp_ta in validated:
                cur=c.execute('INSERT INTO questions(lesson_id,prompt_en,prompt_hi,prompt_ta,options_en,options_hi,options_ta,correct_index,explanation_en,explanation_hi,explanation_ta) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(b.lesson_id,prompt_en,prompt_hi,prompt_ta,json.dumps(opts,ensure_ascii=False),json.dumps(opts_hi,ensure_ascii=False),json.dumps(opts_ta,ensure_ascii=False),correct,exp_en,exp_hi,exp_ta))
                created.append(cur.lastrowid)
            return {'ok':True,'created_count':len(created),'question_ids':created,'provider':'Ollama local AI','review_required':True}
        except Exception as e:
            raise HTTPException(503,'AI quiz generation needs a working local Ollama model. Start Ollama and confirm OLLAMA_MODEL is downloaded. No reliable quiz was generated. Details: '+str(e)[:240])

@app.post('/api/rewards/activity')
def reward_activity(b:RewardActivityBody,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization)
    if u['role']!='student':raise HTTPException(403,'Student account required.')
    if b.activity not in ('read','listen'):raise HTTPException(422,'Unsupported reward activity.')
    with db() as c:
        lesson=c.execute('SELECT grade,published FROM lessons WHERE id=?',(b.lesson_id,)).fetchone()
        if not lesson or not lesson['published']:raise HTTPException(404,'Lesson not found.')
        if lesson['grade']!=u.get('grade'):raise HTTPException(403,'This lesson is outside your grade portal.')
        cur=c.execute('INSERT OR IGNORE INTO reward_events(user_id,activity_key,event_day,stars) VALUES(?,?,?,?)',(u['id'],f'{b.activity}:{b.lesson_id}',date.today().isoformat(),2))
        awarded=2 if cur.rowcount else 0
        if awarded:c.execute('UPDATE users SET stars=stars+? WHERE id=?',(awarded,u['id']))
        row=c.execute('SELECT stars,avatar FROM users WHERE id=?',(u['id'],)).fetchone()
        return {'ok':True,'awarded':awarded,'star_points':row['stars'],'avatar_id':row['avatar']}

@app.post('/api/profile/avatar')
def set_profile_avatar(b:AvatarBody,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization)
    if u['role']!='student':raise HTTPException(403,'Student account required.')
    if b.avatar_id not in AVATARS:raise HTTPException(422,'Choose a listed avatar.')
    with db() as c:
        row=c.execute('SELECT stars FROM users WHERE id=?',(u['id'],)).fetchone();avatar=AVATARS[b.avatar_id]
        if row['stars']<avatar['required']:raise HTTPException(403,f'Collect {avatar["required"]} stars to unlock this character.')
        c.execute('UPDATE users SET avatar=? WHERE id=?',(b.avatar_id,u['id']))
        key=authorization.split(' ',1)[1]
        if key in SESSIONS:SESSIONS[key]['avatar']=b.avatar_id
        return {'ok':True,'avatar_id':b.avatar_id,'avatar':avatar,'star_points':row['stars']}

@app.post('/api/import-content')
def import_content(b:ImportContentBody,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization);teacher(u)
    if b.subject not in ('English','Mathematics','Science','Social Studies','Tamil'):raise HTTPException(422,'Choose a supported subject.')
    if u.get('grade') and b.grade!=u.get('grade'):raise HTTPException(403,'This teacher account is assigned to a different grade.')
    if not b.text.strip():raise HTTPException(422,'No readable text was extracted from the file.')
    raw=b.text[:30000]
    clean_title=(b.title_en or Path(b.filename).stem.replace('_',' ').replace('-',' ').strip() or 'Learning adventure')[:120]
    visual_list=default_visuals(b.subject,clean_title,raw)
    child_body=tidy_for_children(raw,b.grade)
    ai_used=False
    try:
        prompt=f'''You are an experienced primary-school teacher. Rewrite this material into a clear, accurate, engaging lesson for Grade {b.grade} children in the subject {b.subject}. Keep facts grounded in the source; do not invent facts. Use short paragraphs, simple words, small headings if useful, and one or two everyday examples. Remove page numbers, repeated headers, and non-learning clutter. Return strict JSON with keys title_en, body_en, visuals. visuals must contain exactly four items; every item has emoji (one or two emoji characters), title (max 7 words), caption (one child-friendly sentence). Make cards represent different ideas actually present in the source.
Title hint: {clean_title}
Source material:
{raw[:18000]}'''
        generated=parse_json_object(local_ollama(prompt,timeout=120,json_mode=True))
        generated_body=str(generated.get('body_en') or '').strip()[:12000]
        if generated_body:
            child_body=generated_body
            clean_title=str(generated.get('title_en') or clean_title).strip()[:120]
            ai_used=True
        candidate=generated.get('visuals')
        if isinstance(candidate,list):
            valid=[]
            for v in candidate:
                if isinstance(v,dict) and v.get('emoji') and v.get('title') and v.get('caption'):
                    valid.append({'emoji':str(v['emoji'])[:8],'title':str(v['title'])[:80],'caption':str(v['caption'])[:220]})
            if len(valid)>=3:visual_list=(valid+default_visuals(b.subject,clean_title,raw))[:4]
    except Exception:
        pass
    if not child_body:raise HTTPException(422,'The file contained no usable text. Try a text-based PDF or DOCX, or paste the lesson text manually.')
    def maybe_translate(text,target):
        try:
            result=local_ollama(f'Translate this primary-school learning lesson into {target}. Preserve the meaning and child-friendly wording. Return only the translation.\n\n{text[:9000]}',timeout=90)
            return result.strip() or text
        except Exception:return text
    body_hi=maybe_translate(child_body,'Hindi');body_ta=maybe_translate(child_body,'Tamil')
    title_hi=maybe_translate(clean_title,'Hindi') if ai_used else clean_title
    title_ta=maybe_translate(clean_title,'Tamil') if ai_used else clean_title
    picture=visual_list[0]['emoji'] if visual_list else '🌈'
    with db() as c:
        if b.mode=='append':
            if not b.lesson_id:raise HTTPException(422,'Select the lesson that should receive this material.')
            existing=c.execute('SELECT * FROM lessons WHERE id=?',(b.lesson_id,)).fetchone()
            if not existing:raise HTTPException(404,'Selected lesson was not found.')
            if existing['grade']!=b.grade or existing['subject']!=b.subject:raise HTTPException(422,'Selected lesson must match the selected grade and subject.')
            if u.get('grade') and existing['grade']!=u.get('grade'):raise HTTPException(403,'You cannot edit a different grade.')
            label=Path(b.filename).name or 'uploaded material'
            new_en=(existing['body_en']+'\n\nMore to explore — '+label+'\n'+child_body).strip()
            new_hi=(existing['body_hi']+'\n\nऔर जानें — '+label+'\n'+body_hi).strip()
            new_ta=(existing['body_ta']+'\n\nமேலும் அறிந்துகொள்வோம் — '+label+'\n'+body_ta).strip()
            c.execute('UPDATE lessons SET body_en=?,body_hi=?,body_ta=?,visuals_json=?,picture=? WHERE id=?',(new_en,new_hi,new_ta,json.dumps(visual_list,ensure_ascii=False),picture,b.lesson_id))
            saved_id=b.lesson_id;action='appended'
        elif b.mode=='new':
            cur=c.execute('INSERT INTO lessons(title_en,title_hi,title_ta,subject,grade,body_en,body_hi,body_ta,published,created_by,picture,visuals_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(clean_title,title_hi,title_ta,b.subject,b.grade,child_body,body_hi,body_ta,1,u['id'],picture,json.dumps(visual_list,ensure_ascii=False)))
            saved_id=cur.lastrowid;action='created'
        else:raise HTTPException(422,'Choose either new lesson or add to existing lesson.')
        saved=c.execute('SELECT * FROM lessons WHERE id=?',(saved_id,)).fetchone()
        return {'ok':True,'action':action,'lesson':lesson_payload(saved,c),'ai_used':ai_used,'visuals_count':len(visual_list),'translation_note':'AI translation used when local model responded; otherwise source text is retained for teacher review.'}

@app.post('/api/translate')
def translate(payload:dict,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization);teacher(u)
    # Optional local Ollama agent: no content leaves the device. Configure OLLAMA_MODEL, e.g. qwen2.5:3b.
    model=os.getenv('OLLAMA_MODEL','qwen2.5:3b'); text=payload.get('text',''); target=payload.get('target','Tamil')
    if not text.strip():raise HTTPException(422,'Text is required.')
    try:
        req=urllib.request.Request('http://127.0.0.1:11434/api/generate',data=json.dumps({'model':model,'prompt':f'Translate the following primary-school learning content into {target}. Keep meaning, age-appropriate wording and names. Return only the translation.\n\n{text}','stream':False}).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=45) as res: translated=json.loads(res.read()).get('response','').strip()
        if not translated:raise ValueError('Empty translation')
        return {'translated_text':translated,'provider':'local Ollama','review_required':True}
    except Exception:raise HTTPException(503,'AI translation is not ready. Install and start Ollama locally, then download a model. You can still enter translations manually. Always review AI translations before publishing.')
@app.post('/api/upload-content')
async def upload_content(file:UploadFile=File(...),authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization);teacher(u);name=(file.filename or '').lower();raw=await file.read()
    try:
        if name.endswith('.txt') or name.endswith('.md'): content=raw.decode('utf-8-sig')
        elif name.endswith('.docx'):
            from docx import Document
            import io
            content='\n'.join(p.text for p in Document(io.BytesIO(raw)).paragraphs)
        elif name.endswith('.pdf'):
            from pypdf import PdfReader
            import io
            content='\n'.join(p.extract_text() or '' for p in PdfReader(io.BytesIO(raw)).pages)
        else:raise HTTPException(415,'Upload a PDF, DOCX, TXT or MD file.')
    except HTTPException:raise
    except Exception as e:raise HTTPException(400,f'Could not read this file: {e}')
    return {'filename':file.filename,'text':content[:30000],'characters':len(content),'message':'Text extracted. Choose a subject and target lesson, then prepare the lesson with child-friendly text and visual cards.'}


# Desktop/offline mode: serve the compiled React application from the local FastAPI process.
# API routes are registered above this fallback, so /api endpoints remain reachable.
if (FRONTEND_DIR / 'index.html').is_file():
    @app.get('/{asset_path:path}', include_in_schema=False)
    def desktop_frontend_fallback(asset_path: str):
        candidate = (FRONTEND_DIR / asset_path).resolve()
        try:
            candidate.relative_to(FRONTEND_DIR)
        except ValueError:
            raise HTTPException(404, 'Not found')
        if candidate.is_file():
            return FileResponse(candidate)
        # Support client-side React routes with index.html fallback.
        return FileResponse(FRONTEND_DIR / 'index.html')
