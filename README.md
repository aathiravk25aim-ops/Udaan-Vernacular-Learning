# SIH26042 — Vernacular Learning Prototype

A full-stack prototype for mother-tongue-based primary education.

## Stack
- Frontend: React + TypeScript + Vite
- Backend: Python + FastAPI
- Database: SQLite (persistent local file)
- Audio: browser SpeechSynthesis API
- AI assistance: local Ollama model for child-friendly lesson rewriting, English/Hindi/Tamil translation drafts, and AI-generated quiz drafts (optional)
- Lesson visuals: four subject-based animated cartoon cards per bundled/imported lesson, rendered using emoji illustrations and CSS graphics
- Rewards: activity-based Sparkle Stars, animated learning buddy and unlockable profile characters

> Prototype note: The 75 bundled lessons and quiz content are curated sample learning materials, not a general-purpose machine translation corpus. Browser speech availability and pronunciation depend on the device/browser’s installed voices.

## Requirements
- Python 3.10+
- Node.js 18+

## Quick start on Windows
Open this project folder and double-click `START_UDAAN_WINDOWS.bat`. If that file is missing, try the companion `START_UDAAN_WINDOWS.cmd`; both launchers perform the same setup and neither is intended to delete itself. They install the backend/frontend dependencies the first time and open the API and website in separate terminal windows. Keep both server windows open while using Udaan.

If Windows Security removes a launcher after you run it, open Windows Security → Virus & threat protection → Protection history and inspect the recent event. Do not disable antivirus globally. You can also use the manual backend/frontend commands below.

## Troubleshooting: “Failed to fetch”

The frontend sends `/api` requests through the Vite proxy to FastAPI at `127.0.0.1:8000`, avoiding browser CORS and `localhost`/`127.0.0.1` mismatches. The Windows startup script waits for the backend health endpoint before opening the website.

The app-wide language selector is available on the login screen and inside the app. It changes the main navigation and key interface labels. The language selector inside each lesson is independent: changing the app-wide language does not change the language currently selected inside an open lesson, and the quiz follows the lesson language. Back, Forward and Reload controls are included in the app header.

If login still shows a network error, keep both black server windows open and visit `http://127.0.0.1:8000/api/health`. It should return `{"status":"ok","service":"udaan-api"}`. If it does not, check the **Udaan Backend API** window for a Python or port error, then rerun `START_UDAAN_WINDOWS.bat`.

## Run the backend manually
Open a terminal in this folder:

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

API docs: http://127.0.0.1:8000/docs

## Run the frontend
Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL shown by Vite (usually http://localhost:5173).

## Local demonstration accounts

Login IDs are intentionally not displayed on the login page. This is a local demo account set, not production authentication.

### Grade-wise teacher accounts

- Grade 1: `teacher.g1@udaan.local`
- Grade 2: `teacher.g2@udaan.local`
- Grade 3: `teacher.g3@udaan.local`
- Grade 4: `teacher.g4@udaan.local`
- Grade 5: `teacher.g5@udaan.local`

Password for all five teacher accounts: `Teach@123`. Each teacher sees only their assigned grade and can choose Class A, B or C.

### Student and parent account pattern

There are 5 grades × 3 classes (A/B/C) × 20 students = **300 student accounts**. Students have a roll number such as `G1-A01`. Their login ID follows the roll number pattern: `student.g1a01@udaan.local`, `student.g1b01@udaan.local`, or `student.g1c01@udaan.local`; update the grade digit for Grades 2–5. Password for student accounts: `Learn@123`.

Every demo student has a linked parent login, for example `parent.g1a01@udaan.local`, `parent.g1b01@udaan.local`, or `parent.g1c01@udaan.local`. Use the same grade/class/roll pattern as the child. Password for parent accounts: `Parent@123`. The parent's dashboard displays the linked child's name, standard, class and roll number.

The project includes **sample attendance for the latest five school weekdays**, not live school attendance. Quiz attempts and scores are actual local-app activity; weekly report scores remain empty until each sample student completes quizzes.

## Teacher Quiz Workshop

Teachers do not take quizzes from the lesson card. Choose **Create quiz** on a lesson card or open **Quiz workshop** in the sidebar. Select the lesson and choose one mode:

- **Create manually** — enter the question in English and optional Hindi/Tamil wording, add 2–6 answer choices per language, select the correct choice, and add explanations. Save each question; repeat to build the quiz.
- **AI-generated** — request 3, 5, 8 or 10 draft questions from the selected lesson. This needs Ollama running with the configured model. The AI-generated questions must be reviewed by a teacher before students use them. If Ollama is unavailable, use manual creation.

## Upload material into a lesson

In **Teacher studio**, upload a text-based PDF, DOCX, TXT or Markdown file. After extraction, select the subject and choose **Create a new lesson** or **Add to an existing lesson**. When adding to an existing lesson, select the matching lesson; the subject and grade must match. Choose a clear lesson title when creating a new lesson, then select **Create lesson from file** / **Add content to lesson**. The backend tries to rewrite the source into age-appropriate text, create four visual learning cards and prepare translations through local Ollama. Without Ollama, the extracted text is cleaned into short paragraphs and subject-specific visual cards are provided, but this fallback is not a true AI rewrite or verified translation. Review and correct the text before assigning it.

Scanned/image-only PDFs may not contain extractable text; OCR is not included. The visual cards are colourful cartoon-style emoji/CSS illustrations, not automatically downloaded photographs.

## Class graphs and Sparkle Stars

The teacher progress page loads separate **Class A, Class B and Class C** cards comparing average weekly attendance and quiz scores. Attendance in the demo is sample data, not real attendance. Students earn Sparkle Stars for a lesson read, listening to a lesson, and quiz activity (the quiz reward is limited to once per lesson each day; a perfect result can award a bonus). Completing an assigned lesson can give an additional reward. Stars unlock profile buddies at 0, 25, 60, 100, 180 and 300 stars. Rewards are designed for encouragement, not ranking or punishment.

## AI translation agent (local-first)

Teacher-created lessons can be authored in one language; on Save, the app attempts to translate missing title/content fields into English, Hindi and Tamil. Teacher PDF / DOCX / TXT / Markdown uploads extract the text into the lesson editor and attempt Hindi/Tamil translation using a local Ollama model at `http://127.0.0.1:11434`. After reviewing and saving the lesson, students can read the content and use the lesson Listen button for browser text-to-speech. Install Ollama, then run:

```bash
ollama pull qwen2.5:3b
ollama serve
```

Keep Ollama running when using automatic translation. If it is unavailable, the source-language lesson can still be saved; fill missing translations manually or start Ollama and retry. Review all AI drafts before publishing. Preloaded lessons and quizzes work without Ollama.


## Included
- Role-based demo login for students, parents and teachers
- Five locked student grade portals (Grades 1–5), each with 5 subjects × 3 lessons (75 lessons total)
- Picture/emoji-led lesson cards and reading views
- English, Hindi and Tamil content with browser audio
- Student lesson library and English/Hindi/Tamil language toggle
- Browser text-to-speech
- Subject-specific, grade-scaled quizzes with automatic scoring and answer explanations for both correct and incorrect answers
- Grade-wise teacher dashboard: Classes A/B/C, 20 roll-numbered students per class, weekly attendance, quizzes and scores
- Parent view for linked child's attendance, weekly activity, assignments, due dates, quiz history and scores
- Daily quiz quest with child-friendly animated characters and a learning-day streak
- Teacher lesson studio with class-section assignment (one assignment is created for every student in the selected class), file-to-lesson mapping, four colourful subject-based visual cards, and optional local-AI child-friendly rewriting/translation
- Teacher Quiz Workshop for manually authored questions or optional AI-generated quiz drafts (teacher review required)
- Class A/B/C graph cards for weekly average attendance and quiz score
- Sparkle Stars for reading, listening and quiz activity; dancing character and unlockable avatar profiles
- SQLite persistence
- API validation and password hashing

## Production hardening before public deployment
This is a hackathon prototype, not a production identity system. Before real use:
- Replace demo authentication with secure, expiring sessions/JWT and refresh/revocation policy.
- Add rate limiting, CSRF/CORS review, HTTPS, secrets from environment variables, and audit logs.
- Use a managed database and backups for deployment.
- Obtain consent and minimize student data; do not collect unnecessary personal details.
- Have educators verify every translation, lesson, and quiz before children use it.
- Add accessibility testing and validate browser speech support on target devices.

## Latest UI updates
- A persisted app-wide Light / Dark mode switch appears on both login and signed-in pages. It styles student, parent, teacher, lesson, quiz, forms, reports, and dialogs.
- All signed-in roles use one top-navigation sign-out control; the duplicate sidebar-bottom control has been removed.
- The four Picture Explorer cards are interactive buttons. Selecting a card opens its details and offers a listen action.
- The daily learning streak includes a bundled cartoon astronaut-boy SVG companion with a green celebratory animation. Tapping the mascot plays the celebration but does not falsely increase the saved streak; streaks still depend on recorded learning activity.
- Student home includes colourful clickable subject shortcuts inspired by the attached dashboard reference. Quiz answer choices use picture clues, a circular progress indicator and a friendly bundled owl SVG; answers still need to be checked before results are confirmed.

## UI testing note
The updated TypeScript/JSX was syntax-transpiled successfully and the stylesheet braces were checked. A complete Vite production build was not run because dependency installation timed out in the current build environment. Use `npm install` and `npm run build` in `frontend` on the development machine to complete the browser build check.


## Windows offline desktop app (new)

The desktop packaging scaffold is in the `desktop` folder. It wraps the same React + FastAPI app in a Windows desktop window and stores its SQLite database in the current Windows user's application-data folder. Once the installer has been built, the core bundled lessons, quiz bank, account flows, assignments, saved quiz progress, local attendance sample, themes and rewards can run without a live internet connection.

### Build the installer (Windows)

1. Extract this project ZIP fully; keep `frontend`, `backend`, `desktop`, and `BUILD_UDAAN_OFFLINE_APP.ps1` together in the main project folder.
2. Connect to the internet for this one-time build because npm/Python packaging tools and Electron must be downloaded.
3. In File Explorer, double-click `BUILD_UDAAN_OFFLINE_APP.bat`. It opens PowerShell and keeps the window open so you can read any build errors. Do not turn off Windows Security.
4. The build script builds the React frontend, packages the FastAPI backend into a local Windows executable, then makes an NSIS installer. The expected installer is in `desktop\release\Udaan-Learning-Setup-1.0.0.exe`.
5. Install Udaan Learning and open it from the Start Menu or desktop shortcut. Its local database lives in Electron's application-data folder; deleting the installed application does not necessarily delete that data.

### What works offline, and what needs one-time setup

- The app itself has no runtime cloud API dependency for its built-in learning content. Frontend assets and backend packages are bundled.
- SQLite progress and user data are stored locally on the computer running the app. This is a separate database from the existing developer website data.
- Browser/device voices vary. Text-to-speech needs an installed voice for the selected language; a voice may not be installed for every language on every device.
- AI translation, child-friendly AI rewrite, and AI quiz generation use local Ollama at `127.0.0.1:11434`. To use these fully offline, install Ollama and download the configured model once while connected to the internet; after that the downloaded local model can be used without an internet connection, while Ollama is running. The AI model is not embedded in the Windows installer, to avoid making the installer several gigabytes larger.
- The build script has to be run once on Windows with a working internet connection. After the installer is created, normal app use does not require the internet except when obtaining/updating the AI model or updating the app.

### Notes

- The build machine should have the same supported Python/Node.js prerequisites as the web project and enough free disk space for temporary packaging files.
- This is a first desktop packaging pass. Before classroom deployment, test login roles, file uploads, offline restart, database persistence, text-to-speech voices and every screen on the target laptop.
- If the build stops, keep the PowerShell window open and share the final error lines.
#   U d a a n - V e r n a c u l a r - L e a r n i n g  
 