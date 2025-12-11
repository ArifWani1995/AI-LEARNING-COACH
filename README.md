# 🎓 AI Learning Coach

A comprehensive AI-powered personal learning assistant with adaptive learning paths, spaced repetition, and weakness detection.

## ✨ Features

- **📊 Personalized Dashboard** - Track your progress, streaks, and learning stats
- **📚 Knowledge Graph** - Intelligently organized topics with prerequisites
- **📝 Adaptive Quizzes** - Diagnostic tests, practice quizzes, and reviews
- **🔄 Spaced Repetition** - SM-2 algorithm for optimal review scheduling
- **🎯 Weakness Detection** - ML-powered analysis of learning gaps
- **📅 Study Plans** - Short-term and long-term learning roadmaps
- **📄 PDF Reports** - Generate detailed progress reports

## 🏗️ Project Structure

```
ai-learning-coach/
├── backend/
│   ├── main.py                    # FastAPI server
│   ├── requirements.txt           # Python dependencies
│   ├── database/
│   │   └── db.py                  # SQLite configuration
│   ├── models/
│   │   └── user.py                # SQLAlchemy models
│   └── services/
│       ├── knowledge_graph.py     # Topic relationships
│       ├── spaced_repetition.py   # SM-2 algorithm
│       ├── quiz_generator.py      # Quiz creation & grading
│       ├── weakness_detector.py   # ML weakness analysis
│       └── pdf_generator.py       # Report generation
├── frontend/
│   ├── index.html                 # Main dashboard
│   ├── css/
│   │   └── styles.css             # Premium dark theme
│   └── js/
│       └── app.js                 # Frontend logic
└── data/
    └── knowledge_base.json        # Topics & questions
```

## 🚀 Getting Started

### Backend Setup

1. Navigate to the backend directory:
```bash
cd ai-learning-coach/backend
```

2. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

Simply open `frontend/index.html` in your browser, or use a local server:

```bash
cd ai-learning-coach/frontend
python -m http.server 3000
```

Then visit `http://localhost:3000`

## 📡 API Endpoints

### Users
- `POST /api/users` - Create user
- `GET /api/users/{id}` - Get user profile
- `PUT /api/users/{id}` - Update user

### Topics
- `GET /api/topics` - List all topics
- `GET /api/topics/{id}` - Get topic details
- `GET /api/topics/{id}/learning-path` - Get optimal learning path

### Quizzes
- `POST /api/quiz/diagnostic` - Generate diagnostic quiz
- `POST /api/quiz/practice` - Generate practice quiz
- `POST /api/quiz/submit` - Submit quiz answers

### Progress
- `GET /api/users/{id}/progress` - Get learning progress
- `POST /api/users/{id}/progress` - Update topic progress
- `GET /api/users/{id}/review-schedule` - Get spaced repetition schedule

### Analysis
- `GET /api/users/{id}/weaknesses` - Analyze learning weaknesses
- `POST /api/users/{id}/study-plan` - Create study plan
- `GET /api/users/{id}/report` - Generate PDF report

## 🔧 Configuration

### Adding New Topics

Edit `data/knowledge_base.json`:

```json
{
  "id": "your_topic_id",
  "name": "Topic Name",
  "description": "Topic description",
  "category": "Programming",
  "difficulty_level": 2,
  "prerequisites": ["prerequisite_topic_id"],
  "questions": [
    {
      "id": "q1",
      "question_type": "multiple_choice",
      "difficulty": "medium",
      "question_text": "Your question?",
      "options": ["A", "B", "C", "D"],
      "correct_answer": "B",
      "concept_tags": ["concept1"],
      "points": 2
    }
  ]
}
```

## 📊 Algorithms Used

### Spaced Repetition (SM-2)
The SuperMemo 2 algorithm optimizes review intervals based on:
- Quality of recall (0-5 rating)
- Ease factor (individual difficulty)
- Number of successful repetitions

### Weakness Detection
Pattern analysis identifies:
- Low-performing topics
- Struggling concepts
- Performance trends (improving/declining)

### Knowledge Graph
Topological sorting ensures:
- Prerequisites are learned first
- Optimal learning paths
- Gap identification

## 🎨 Design Features

- **Dark Theme** with glassmorphism effects
- **Animated Background** with floating gradients
- **Micro-animations** for enhanced UX
- **Responsive Design** for all devices
- **Premium Typography** using Inter font

## 📝 License

MIT License - Feel free to use and modify!

---

Built with ❤️ using FastAPI, SQLAlchemy, and vanilla JavaScript
