"""Portfolio content: experience, projects, achievements.

Kept as plain Python data for now. Phase 2 moves this into Postgres; Phase 4
feeds the same records into the RAG chatbot's vector store.
"""

EXPERIENCE = [
    {
        "company": "Hexango Pvt Ltd",
        "role": "Data & Analytics / AI Intern",
        "period": "Jan 2026 – May 2026",
        "location": "Bengaluru (Remote)",
        "points": [
            "Led migration of an enterprise database from AWS RDS SQL Server to PostgreSQL, "
            "designing and running ETL pipelines inside Scrum sprints to keep data consistent.",
            "Re-engineered T-SQL procedures into optimised PL/pgSQL, improving performance and "
            "maintainability of backend workflows.",
            "Built a Python synthetic-data generator producing 250K+ relational records with full "
            "referential integrity.",
        ],
    },
]

PROJECTS = [
    {
        "slug": "distributed-web-scraper",
        "name": "Distributed Web Scraper Platform",
        "blurb": "Queue-based backend that runs web-scraping jobs asynchronously across workers.",
        "stack": ["FastAPI", "PostgreSQL", "Redis + RQ", "SQLAlchemy", "BeautifulSoup"],
        "highlights": [
            "REST API to submit URLs and poll job status (pending → processing → completed).",
            "Redis-backed queue with a pool of parallel worker processes.",
            "Results persisted to PostgreSQL via SQLAlchemy.",
        ],
        "repo": "https://github.com/PradyumnaPrasad/Distributed_WebScraper_Platform",
        "tags": ["backend", "distributed-systems"],
    },
    {
        "slug": "neuromentor",
        "name": "NeuroMentor — Adaptive Learning Platform",
        "blurb": "Personalised tutoring that adapts difficulty with reinforcement learning.",
        "stack": [
            "FastAPI",
            "MongoDB",
            "PyTorch (Q-Learning)",
            "Google Gemini",
            "React",
            "TypeScript",
        ],
        "highlights": [
            "Q-Learning agent scales question difficulty to each student's mastery.",
            "Gemini-generated explanations and adaptive quizzes with real-time feedback.",
            "JWT + bcrypt auth; claimed sub-500ms AI responses and 100+ concurrent users.",
        ],
        "repo": "https://github.com/PradyumnaPrasad/NeuroMentor_AdaptiveLearningPlatform",
        "tags": ["ai-ml", "backend", "full-stack"],
        "team": True,
    },
    {
        "slug": "dual-insight-engine",
        "name": "Dual Insight Engine",
        "blurb": "Dual-corpus RAG that compares two PDFs side by side and cites its sources.",
        "stack": ["Python", "LangChain", "ChromaDB", "Google Gemini", "Streamlit", "pypdf"],
        "highlights": [
            "Two independent ChromaDB collections with parallel retrieval per query.",
            "Structured JSON output for reliable parsing and auto-generated charts.",
            "Answers carry page-number citations back to the source document.",
        ],
        "repo": "https://github.com/PradyumnaPrasad/Dual_Insight_Engine",
        "tags": ["ai-ml", "rag"],
    },
    {
        "slug": "ai-resume-maker",
        "name": "AI Resume Maker",
        "blurb": "Parses an existing résumé, mines GitHub, and generates a tailored one-pager.",
        "stack": ["FastAPI", "Streamlit", "LangChain", "Gemini 1.5 Flash", "SQLite", "ReportLab"],
        "highlights": [
            "PDF résumé parser that pre-fills every section automatically.",
            "GitHub analyzer that pulls project summaries from repo READMEs.",
            "Skill categoriser and job-description-tailored summary writer.",
        ],
        "repo": "https://github.com/PradyumnaPrasad/AI-ResumeMaker",
        "tags": ["ai-ml", "backend"],
    },
    {
        "slug": "isl-gesture-detection",
        "name": "Indian Sign Language Gesture Detection",
        "blurb": "Real-time recognition of ISL alphabets and numerals from a webcam feed.",
        "stack": ["MediaPipe", "TensorFlow / Keras", "OpenCV", "scikit-learn", "NumPy"],
        "highlights": [
            "21 hand keypoints (63 coords) per frame via MediaPipe.",
            "Dense network with dropout across 35 gesture classes (A–Z, 1–9).",
            "Majority-vote smoothing across frames for stable predictions.",
        ],
        "repo": "https://github.com/PradyumnaPrasad/Gesture_Detection",
        "tags": ["ai-ml", "computer-vision"],
    },
]

ACHIEVEMENTS = [
    "1st Prize — Open Innovation Track, 48-hour MIT National Hackathon 2025 (300+ teams).",
    "1st Prize — SIT Pitchathon 2025 and 2026.",
    "Solved 400+ DSA problems on LeetCode (arrays, sliding window, greedy, and more).",
    "Lead — AI Brewery club (Aug 2024–present): ran 50+ hackathons and workshops end to end.",
]

EDUCATION = [
    {
        "what": "B.E. Computer Science & Engineering (AI & ML)",
        "where": "Siddaganga Institute of Technology",
        "period": "Aug 2023 – Jul 2027",
        "note": "CGPA 9.12",
    },
    {
        "what": "Pre-University (12th)",
        "where": "PU College",
        "period": "2021 – 2023",
        "note": "96%",
    },
]
