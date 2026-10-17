# 🚀 Udaan — Vernacular Learning Platform

> **Learn in the language you understand. Learn at your own pace. Learn without depending on the internet.**

**Udaan** is an offline-first, multilingual learning platform designed to make primary education more accessible through **English, Hindi, and Tamil** learning content.

The platform combines interactive lessons, multilingual audio, quizzes, rewards, teacher tools, parent monitoring, local AI assistance, and a Windows desktop application into one child-friendly learning environment.

---

## 🏆 Project Information

| Category | Details |
|---|---|
| Project Name | **Udaan – Vernacular Learning Platform** |
| SIH Problem Statement | **SIH26042** |
| Application Type | Education / EdTech |
| Target Users | Students, Teachers & Parents |
| Supported Languages | English 🇬🇧, Hindi 🇮🇳, Tamil 🇮🇳 |
| Learning Levels | Grade 1 – Grade 5 |
| Bundled Lessons | 75 |
| Platform | Web + Windows Desktop |
| Architecture | Full Stack |
| AI Approach | Local-first AI with Ollama |
| Database | SQLite |

---

## 🌟 Why Udaan?

Many primary-school learners understand concepts more effectively when learning materials are available in a familiar language.

However, digital learning environments can face challenges such as:

- Heavy dependence on English.
- Limited availability of regional-language educational content.
- Internet dependency.
- Limited personalized learning support.
- Difficulty for teachers to create and manage content.
- Limited visibility for parents into their child's learning progress.

**Udaan addresses these challenges through a multilingual, offline-first learning environment.**

Students can read lessons, listen to supported lesson audio, practice quizzes, earn rewards, and track their learning activity.

Teachers can create lessons, upload learning materials, create quizzes, assign content, and monitor class progress.

Parents can monitor their child's attendance, assignments, quiz history, and learning activity.

---

# 🎯 Key Features

## 👩‍🎓 Student Learning

- Grade-based learning environment.
- Five student grade portals.
- Subject-wise lesson organization.
- English, Hindi and Tamil content.
- Multilingual lesson switching.
- Offline lesson audio for bundled content.
- Interactive lesson visuals.
- Picture/emoji-based learning cards.
- Interactive quizzes.
- Automatic quiz scoring.
- Answer explanations.
- Daily quiz quest.
- Learning-day streak.
- Sparkle Stars reward system.
- Unlockable profile buddies/characters.
- Student learning activity tracking.

---

## 👨‍🏫 Teacher Portal

Teachers can manage learning content and monitor student progress.

### Teacher features

- Grade-wise teacher accounts.
- Class A / B / C management.
- Lesson assignment.
- Lesson creation.
- Lesson editing.
- PDF/DOCX/TXT/Markdown material upload.
- Automatic text extraction.
- Multilingual content preparation.
- Subject-specific visual learning cards.
- Manual quiz creation.
- AI-generated quiz drafts.
- Quiz review before publishing.
- Weekly attendance monitoring.
- Quiz performance monitoring.
- Class-level progress graphs.
- Student activity monitoring.

---

## 👨‍👩‍👧 Parent Portal

Parents can view the learning progress of their linked child.

### Parent features

- Linked-child dashboard.
- Student information.
- Attendance overview.
- Weekly learning activity.
- Assignments.
- Due dates.
- Quiz history.
- Quiz scores.
- Learning progress.

---

# 🌍 Multilingual Learning

Udaan supports three learning languages:

### 🇬🇧 English

English lesson content and audio.

### 🇮🇳 Hindi

Hindi lesson content and bundled offline lesson audio.

### 🇮🇳 Tamil

Tamil lesson content and bundled offline lesson audio.

The lesson language selector is independent from the application-wide interface language.

Students can therefore change the language used inside an individual lesson without changing the entire application interface.

---

# 🔊 Offline Multilingual Audio

One of the important features of Udaan is its **offline lesson audio**.

Supported bundled lesson audio:

```text
English 🇬🇧
       ↓
Hindi 🇮🇳
       ↓
Tamil 🇮🇳
```

The supported lesson audio is packaged with the application so students can listen to lessons without requiring a live internet connection.

This is particularly useful in environments where:

- Internet connectivity is limited.
- Students use shared computers.
- Schools have unreliable network access.
- Learning needs to continue without cloud services.

> **Note:** Teacher-created lessons that do not have a bundled recording can use the available device/browser speech fallback where supported.

---

# 🤖 Local AI Assistance

Udaan includes an optional **local-first AI layer** using Ollama.

AI assistance can be used for:

- Child-friendly lesson rewriting.
- English/Hindi/Tamil translation drafts.
- AI-generated quiz drafts.

The AI service is accessed locally through:

```text
http://127.0.0.1:11434
```

A configured Ollama model can be downloaded once and subsequently used locally.

### Example

```text
Teacher uploads learning material
          ↓
Text extraction
          ↓
Local AI processing
          ↓
Child-friendly content
          ↓
Translation drafts
          ↓
Teacher review
          ↓
Lesson published
```

AI-generated educational content should always be reviewed by a teacher before being provided to students.

---

# 📚 Lesson Content

The prototype contains:

```text
5 Grades
   ×
5 Subjects
   ×
3 Lessons
   =
75 Bundled Lessons
```

The bundled lessons are curated sample educational materials for demonstration and prototype purposes.

They are not intended to represent a complete curriculum or general-purpose translation dataset.

---

# 📝 Interactive Quiz System

Students can reinforce learning through subject-specific quizzes.

### Quiz features

- Multiple-choice questions.
- Language-aware questions.
- Automatic scoring.
- Correct/incorrect answer feedback.
- Answer explanations.
- Picture clues.
- Circular quiz progress indicator.
- Grade-scaled quizzes.
- Daily quiz quest.
- Quiz activity rewards.

### Teacher Quiz Workshop

Teachers can create quizzes in two ways:

**Manual Creation**

Teachers can enter:

- Questions.
- Language-specific wording.
- Answer choices.
- Correct answers.
- Explanations.

**AI Generation**

Teachers can request draft questions using the local AI system.

Available draft sizes include:

```text
3 questions
5 questions
8 questions
10 questions
```

AI-generated questions must be reviewed by the teacher before students use them.

---

# ⭐ Gamification & Rewards

Udaan uses a child-friendly reward system to encourage learning.

Students can earn **Sparkle Stars** through learning activities such as:

- Reading lessons.
- Listening to lessons.
- Completing quizzes.
- Completing assigned lessons.

The system includes:

```text
0 Stars
25 Stars
60 Stars
100 Stars
180 Stars
300 Stars
```

These milestones can unlock profile buddies/characters.

The reward system is designed for **encouragement rather than ranking or punishment**.

---

# 📊 Learning Progress

Teachers can monitor class-level progress through separate:

```text
Class A
Class B
Class C
```

progress cards.

The dashboard can display:

- Average weekly attendance.
- Quiz performance.
- Student activity.
- Learning progress.

The prototype includes sample attendance data for demonstration.

---

# 🎨 Child-Friendly UI

Udaan is designed with younger learners in mind.

The interface includes:

- Colourful subject shortcuts.
- Picture-based learning cards.
- Emoji/CSS illustrations.
- Animated learning buddy.
- Friendly quiz visuals.
- Progress indicators.
- Sparkle Stars.
- Unlockable characters.
- Light/Dark mode.
- Responsive application layout.

The goal is to make learning feel more interactive and less like a traditional classroom worksheet.

---

# 🏗️ System Architecture

```text
                         ┌──────────────────────┐
                         │        UDAAN         │
                         │ Vernacular Learning  │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
        👩‍🎓 Student            👨‍🏫 Teacher          👨‍👩‍👧 Parent
              │                     │                     │
              └─────────────────────┼─────────────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ React + TypeScript   │
                         │        + Vite        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      FastAPI         │
                         │       Backend        │
                         └──────────┬───────────┘
                                    │
                    ┌───────────────┼────────────────┐
                    │               │                │
                    ▼               ▼                ▼
                 SQLite         Offline Audio    Local AI
                 Database         Assets          Ollama
                    │               │                │
                    └───────────────┼────────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Windows Desktop App  │
                         │       Electron       │
                         └──────────────────────┘
```

---

# 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React |
| Language | TypeScript |
| Frontend Build | Vite |
| Backend | Python |
| API Framework | FastAPI |
| Database | SQLite |
| Desktop Framework | Electron |
| AI | Ollama |
| Styling | CSS |
| Audio | Bundled offline audio + device/browser fallback |
| Packaging | Windows NSIS |
| Development | VS Code |
| Version Control | Git + GitHub |

---

# 📁 Project Structure

```text
Udaan-Vernacular-Learning/
│
├── 📁 backend/
│   ├── app.py
│   ├── requirements.txt
│   └── ...
│
├── 📁 frontend/
│   ├── 📁 src/
│   ├── 📁 public/
│   │   └── 📁 audio/
│   ├── package.json
│   └── ...
│
├── 📁 desktop/
│   └── ...
│
├── 📄 .gitignore
│
├── 📄 BUILD_UDAAN_OFFLINE_APP.bat
├── 📄 BUILD_UDAAN_OFFLINE_APP.ps1
│
├── 📄 START_UDAAN_WINDOWS.bat
├── 📄 START_UDAAN_WINDOWS.cmd
│
└── 📄 README.md
```

---

# ⚙️ Requirements

For development:

```text
Python 3.10+
Node.js 18+
npm
Git
Windows 10/11
```

For optional AI functionality:

```text
Ollama
Configured local AI model
```

---

# 🚀 Quick Start — Windows

The easiest way to start the development application is:

```text
START_UDAAN_WINDOWS.bat
```

Double-click the file from the project folder.

The launcher starts the backend and frontend and opens the application.

Keep the server windows open while using the development version.

---

# 🔧 Manual Backend Setup

Open a terminal in the project directory.

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start FastAPI:

```bash
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/api/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "udaan-api"
}
```

---

# 💻 Manual Frontend Setup

Open a second terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Open the local URL displayed by Vite.

The default development URL is usually:

```text
http://localhost:5173
```

---

# 🖥️ Build the Windows Desktop Application

Udaan includes a Windows desktop packaging system.

### Step 1

Extract the complete project.

Make sure these folders/files are together:

```text
frontend/
backend/
desktop/
BUILD_UDAAN_OFFLINE_APP.ps1
BUILD_UDAAN_OFFLINE_APP.bat
```

### Step 2

Connect the computer to the internet for the initial build.

The build process may need to download:

- npm packages.
- Python packaging tools.
- Electron dependencies.
- Other build dependencies.

### Step 3

Double-click:

```text
BUILD_UDAAN_OFFLINE_APP.bat
```

### Step 4

Wait for the build to complete.

### Step 5

The expected installer is:

```text
desktop/release/Udaan-Learning-Setup-1.0.0.exe
```

### Step 6

Install the generated Windows application.

After installation, the bundled learning content and supported offline functionality can be used without a live internet connection.

---

# 📦 Windows Release

The recommended distribution format is a Windows installer.

```text
Udaan-Learning-Setup-1.0.0.exe
```

The installer packages the desktop application together with the required local application components.

For public distribution, the installer can be published through **GitHub Releases**.

---

# 🔑 Demo Accounts

The prototype contains local demonstration accounts.

## Teacher Accounts

| Grade | Login |
|---|---|
| Grade 1 | `teacher.g1@udaan.local` |
| Grade 2 | `teacher.g2@udaan.local` |
| Grade 3 | `teacher.g3@udaan.local` |
| Grade 4 | `teacher.g4@udaan.local` |
| Grade 5 | `teacher.g5@udaan.local` |

Teacher password:

```text
Teach@123
```

Teachers can select:

```text
Class A
Class B
Class C
```

---

## Student Accounts

There are:

```text
5 Grades
×
3 Classes
×
20 Students
=
300 Student Accounts
```

Example:

```text
student.g1a01@udaan.local
```

Student password:

```text
Learn@123
```

Roll number example:

```text
G1-A01
```

---

## Parent Accounts

Example:

```text
parent.g1a01@udaan.local
```

Parent password:

```text
Parent@123
```

Each demonstration parent account is associated with a corresponding child account.

> These are demonstration credentials for the prototype and should not be used for a production deployment.

---

# 🤖 Setting Up Ollama

Ollama is optional for the core bundled learning experience.

Install Ollama and download the configured model:

```bash
ollama pull qwen2.5:3b
```

Start Ollama:

```bash
ollama serve
```

The application expects the local service at:

```text
http://127.0.0.1:11434
```

Ollama is used for optional:

- Lesson rewriting.
- Translation drafts.
- Quiz generation.

The AI model is not embedded into the Windows installer because doing so would significantly increase installer size.

---

# 📄 Teacher Material Upload

Teachers can upload:

```text
PDF
DOCX
TXT
Markdown
```

The workflow is:

```text
Upload Material
       ↓
Extract Text
       ↓
Select Subject
       ↓
Create New Lesson
       OR
Add to Existing Lesson
       ↓
AI Processing (Optional)
       ↓
Translation Draft
       ↓
Visual Learning Cards
       ↓
Teacher Review
       ↓
Publish
```

Scanned/image-only PDFs may not contain extractable text because OCR is not included in the current prototype.

---

# 🔐 Privacy & Security

Udaan is currently a **hackathon/educational prototype** and should not be considered a production identity system.

Before real-world deployment, the following should be implemented:

- Secure session-based authentication.
- JWT/refresh-token security where appropriate.
- Password policies.
- Rate limiting.
- HTTPS.
- CSRF/CORS review.
- Secure secret management.
- Audit logging.
- Database backups.
- Role-based access control.
- Student-data minimization.
- Educator review of AI-generated content.
- Accessibility testing.
- Secure production deployment.

The application should collect only the student information necessary for the educational functionality.

---

# 🛡️ Responsible AI

Udaan uses AI as an **assistive tool**, not as an uncontrolled content publisher.

The recommended workflow is:

```text
AI generates draft
       ↓
Teacher reviews
       ↓
Teacher corrects
       ↓
Teacher approves
       ↓
Student receives content
```

This is particularly important for:

- Translation.
- Educational explanations.
- Quiz questions.
- Child-friendly content.

---

# 🌐 Offline-First Design

The core learning experience is designed to minimize internet dependency.

### Available locally

```text
✓ Bundled lessons
✓ Quiz content
✓ Local SQLite database
✓ Supported offline audio
✓ UI assets
✓ Rewards
✓ Student activity
✓ Core application
```

### Optional local AI

```text
Ollama
    ↓
Local model
    ↓
AI assistance
```

The AI model requires a one-time download and must be running locally when AI features are used.

---

# 📈 Learning Flow

```text
                    STUDENT LOGIN
                         │
                         ▼
                  SELECT GRADE
                         │
                         ▼
                  SELECT SUBJECT
                         │
                         ▼
                   SELECT LESSON
                         │
                         ▼
              ┌──────────┴──────────┐
              │                     │
            READ                 LISTEN
              │                     │
              └──────────┬──────────┘
                         ▼
                   TAKE QUIZ
                         │
                         ▼
                   VIEW RESULT
                         │
                         ▼
                 EARN SPARKLE STARS
                         │
                         ▼
                  TRACK PROGRESS
```

---

# 👨‍🏫 Teacher Workflow

```text
Teacher Login
     ↓
Teacher Dashboard
     ↓
Create / Upload Lesson
     ↓
Optional Local AI Processing
     ↓
Review Content
     ↓
Create / Generate Quiz
     ↓
Assign to Class
     ↓
Monitor Student Progress
```

---

# 👨‍👩‍👧 Parent Workflow

```text
Parent Login
     ↓
Linked Child Dashboard
     ↓
Attendance
     ↓
Assignments
     ↓
Learning Activity
     ↓
Quiz History
     ↓
Scores & Progress
```

---

# 🧪 Testing Checklist

Before classroom or hackathon demonstration, verify:

### Student

- [ ] Student login works.
- [ ] Grade selection works.
- [ ] Subject selection works.
- [ ] Lesson opens correctly.
- [ ] English content works.
- [ ] Hindi content works.
- [ ] Tamil content works.
- [ ] English audio works.
- [ ] Hindi audio works.
- [ ] Tamil audio works.
- [ ] Audio works without internet.
- [ ] Quiz opens.
- [ ] Quiz scoring works.
- [ ] Sparkle Stars update.
- [ ] Learning streak works.

### Teacher

- [ ] Teacher login works.
- [ ] Class selection works.
- [ ] Lesson creation works.
- [ ] File upload works.
- [ ] Quiz creation works.
- [ ] Assignment works.
- [ ] Progress dashboard works.

### Parent

- [ ] Parent login works.
- [ ] Correct child is displayed.
- [ ] Attendance is visible.
- [ ] Quiz history is visible.
- [ ] Assignments are visible.

### Desktop

- [ ] Installer builds successfully.
- [ ] Application installs successfully.
- [ ] Application launches.
- [ ] Database persists.
- [ ] Application works after restart.
- [ ] Offline lessons work.
- [ ] Offline audio works.

---

# ⚠️ Current Limitations

Udaan is currently a prototype.

Current limitations include:

- Demonstration attendance data is sample data.
- AI features require local Ollama setup.
- AI-generated educational content requires teacher verification.
- Authentication requires production hardening before public deployment.
- OCR is not included for scanned/image-only documents.
- The packaged desktop release currently targets Windows.
- Additional Indian languages require corresponding content and audio assets.
- Device/browser speech support can vary for fallback speech functionality.

---

# 🚀 Future Enhancements

## 🌏 More Languages

Expand beyond English, Hindi and Tamil:

```text
Telugu
Malayalam
Kannada
Bengali
Marathi
Gujarati
Punjabi
Odia
```

---

## 🎤 Voice-Based Learning

Future versions can include:

- Pronunciation practice.
- Voice questions.
- Speech recognition.
- Reading-aloud evaluation.
- Voice-based navigation.

---

## 🧠 Adaptive Learning

The system can analyze:

```text
Quiz Performance
      +
Lesson Activity
      +
Learning Speed
      +
Repeated Mistakes
      ↓
Personalized Learning Path
```

Students could receive additional practice based on areas where they need improvement.

---

## 📊 Advanced Analytics

Future dashboards could include:

- Individual learning trends.
- Subject-wise performance.
- Language preference analysis.
- Learning difficulty detection.
- At-risk learner identification.
- Teacher intervention recommendations.

---

## 📱 Mobile Application

A future version could provide:

```text
Android
iOS
```

while maintaining the same offline-first learning model.

---

## 🔄 Offline Synchronization

For schools with intermittent connectivity:

```text
Student Device
      ↓
Local Learning Data
      ↓
Internet Available
      ↓
Secure Synchronization
      ↓
Central School Dashboard
```

This would allow students to continue learning offline while synchronizing progress when connectivity becomes available.

---

# 🌱 Social Impact

Udaan aims to support more inclusive digital education by reducing barriers caused by:

- Language preference.
- Internet availability.
- Limited teacher resources.
- Lack of localized digital content.
- Limited parent visibility.

The platform is designed around the idea that **technology should adapt to learners rather than forcing every learner to adapt to one language or learning environment.**

---

# 🎯 Target Users

### Primary

👧👦 Primary-school students

### Secondary

👨‍🏫 Teachers

### Supporting users

👨‍👩‍👧 Parents

### Potential deployment environments

- Government schools.
- Rural schools.
- Low-connectivity educational environments.
- Community learning centers.
- Digital classrooms.
- Home learning environments.

---

# 💡 Project Highlights

```text
🌍 Multilingual
🔊 Offline Audio
📚 75 Bundled Lessons
📝 Interactive Quizzes
⭐ Gamified Learning
👩‍🎓 Student Portal
👨‍🏫 Teacher Portal
👨‍👩‍👧 Parent Portal
🤖 Local AI
💾 SQLite Persistence
🖥️ Windows Desktop App
🔒 Privacy-Aware Design
```
### Login

![Udaan Login](screenshots/login.png)

### Student Dashboard

![Student Dashboard](screenshots/student-dashboard.png)

### Multilingual Lesson

![Multilingual Lesson](screenshots/lesson-hindi.png)

### Interactive Quiz

![Quiz](screenshots/quiz.png)

### Teacher Dashboard

![Teacher Dashboard](screenshots/teacher-dashboard.png)

### Parent Dashboard

![Parent Dashboard](screenshots/parent-dashboard.png)

---

# 🎥 Demo

The recommended demonstration flow is:

```text
1. Student Login
2. Grade Selection
3. Subject Selection
4. Open Lesson
5. English Lesson
6. Switch to Hindi
7. Play Hindi Audio
8. Switch to Tamil
9. Play Tamil Audio
10. Complete Quiz
11. Earn Sparkle Stars
12. Open Teacher Dashboard
13. Show Class Progress
14. Open Parent Dashboard
15. Show Child Progress
16. Disconnect Internet
17. Demonstrate Offline Learning
```

---

# 📦 Releases

The Windows installer can be distributed through GitHub Releases.

Recommended release format:

```text
Udaan Learning v1.0.0
```

Installer:

```text
Udaan-Learning-Setup-1.0.0.exe
```

---

# 🤝 Contributing

Contributions and suggestions are welcome.

A typical contribution workflow:

```bash
git clone <repository-url>

cd Udaan-Vernacular-Learning

git checkout -b feature/your-feature

# Make your changes

git add .

git commit -m "Add your feature"

git push origin feature/your-feature
```

Then create a Pull Request on GitHub.

---

# 📄 License

This project is currently a prototype created for educational and hackathon purposes.

If this project is later released as open source, add an appropriate license such as MIT, Apache-2.0, or another license selected by the project owners.

---

# 👩‍💻 Project

**Udaan — Vernacular Learning Platform**

> **Learn. Listen. Practice. Grow.**

Built with ❤️ using React, TypeScript, Python, FastAPI, SQLite, Electron and local AI.

---

## ⭐ Support the Project

If you find Udaan useful or interesting:

⭐ Star the repository  
🍴 Fork the project  
💡 Suggest improvements  
🐛 Report issues  
🤝 Contribute to the project

---

**Udaan — Making digital learning more accessible, multilingual and offline-friendly.**