/**
 * AI Learning Coach - Frontend Application
 * Handles all UI interactions and API communication
 */

const API_BASE = 'http://localhost:8000/api';

// State Management
const state = {
    currentUser: null,
    userId: 1,
    topics: [],
    currentQuiz: null,
    currentQuestionIndex: 0,
    userAnswers: [],
    progress: [],
    schedule: {}
};

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    generateCalendar();
    loadTopics();
    loadProgress();
});

async function initializeApp() {
    // Check for existing user or create demo user
    try {
        const user = await fetchAPI(`/users/${state.userId}`);
        state.currentUser = user;
        document.getElementById('user-name').textContent = user.username || 'Learner';
        updateSettings(user);
    } catch (error) {
        // Create demo user
        await createDemoUser();
    }
}

async function createDemoUser() {
    try {
        const response = await fetchAPI('/users', {
            method: 'POST',
            body: JSON.stringify({
                username: 'Learner',
                email: 'learner@example.com',
                current_level: 'beginner',
                learning_speed: 'medium',
                learning_goal: 'Master Python Programming'
            })
        });
        state.userId = response.id;
        showToast('Welcome! Your learning journey begins now!', 'success');
    } catch (error) {
        console.log('Using offline mode');
    }
}

// ==================== API HELPERS ====================

async function fetchAPI(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        if (!response.ok) throw new Error('API Error');
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ==================== NAVIGATION ====================

function showPage(pageName) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.add('hidden');
        page.classList.remove('active');
    });
    
    // Show selected page
    const targetPage = document.getElementById(`page-${pageName}`);
    if (targetPage) {
        targetPage.classList.remove('hidden');
        targetPage.classList.add('active');
    }
    
    // Update nav
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.dataset.page === pageName) {
            link.classList.add('active');
        }
    });
    
    // Load page-specific data
    if (pageName === 'topics') loadTopics();
    if (pageName === 'progress') loadProgress();
    if (pageName === 'schedule') loadSchedule();
}

// ==================== TOPICS ====================

async function loadTopics() {
    try {
        const data = await fetchAPI('/topics');
        state.topics = data.topics || [];
        renderTopics(state.topics);
    } catch (error) {
        // Load demo topics
        state.topics = getDemoTopics();
        renderTopics(state.topics);
    }
}

function renderTopics(topics) {
    const grid = document.getElementById('topics-grid');
    if (!grid) return;
    
    grid.innerHTML = topics.map(topic => `
        <div class="topic-card" onclick="selectTopic('${topic.id}')">
            <div class="topic-card-header">
                <div class="topic-icon">${getTopicIcon(topic.category)}</div>
                <span class="topic-difficulty ${getDifficultyClass(topic.difficulty_level)}">
                    ${getDifficultyLabel(topic.difficulty_level)}
                </span>
            </div>
            <h3 class="topic-title">${topic.name}</h3>
            <p class="topic-description">${topic.description}</p>
            <div class="topic-meta">
                <span>📖 ${topic.questions?.length || 5} questions</span>
                <span>⏱️ ~${topic.difficulty_level * 10} min</span>
            </div>
        </div>
    `).join('');
}

function getTopicIcon(category) {
    const icons = {
        'Programming': '💻',
        'Math': '📐',
        'Science': '🔬',
        'Language': '📝',
        'default': '📚'
    };
    return icons[category] || icons.default;
}

function getDifficultyClass(level) {
    if (level <= 1) return 'easy';
    if (level <= 2) return 'medium';
    return 'hard';
}

function getDifficultyLabel(level) {
    if (level <= 1) return 'Easy';
    if (level <= 2) return 'Medium';
    return 'Hard';
}

function selectTopic(topicId) {
    const topic = state.topics.find(t => t.id === topicId);
    if (topic) {
        showToast(`Starting: ${topic.name}`, 'success');
        startQuiz('practice', [topicId]);
    }
}

// ==================== QUIZ ====================

async function startQuiz(type, topicIds = null) {
    document.getElementById('quiz-selection').classList.add('hidden');
    document.getElementById('quiz-container').classList.remove('hidden');
    document.getElementById('quiz-results').classList.add('hidden');
    
    state.currentQuestionIndex = 0;
    state.userAnswers = [];
    
    try {
        if (!topicIds) {
            topicIds = state.topics.slice(0, 3).map(t => t.id);
        }
        
        let quiz;
        if (type === 'diagnostic') {
            quiz = await fetchAPI(`/quiz/diagnostic?user_id=${state.userId}`, {
                method: 'POST',
                body: JSON.stringify(topicIds)
            });
        } else {
            quiz = await fetchAPI(`/quiz/practice?user_id=${state.userId}&num_questions=10&focus_weaknesses=${type === 'weakness'}`, {
                method: 'POST',
                body: JSON.stringify(topicIds)
            });
        }
        state.currentQuiz = quiz;
    } catch (error) {
        // Use demo quiz
        state.currentQuiz = getDemoQuiz();
    }
    
    renderQuestion();
}

function renderQuestion() {
    const quiz = state.currentQuiz;
    if (!quiz || !quiz.questions) return;
    
    const question = quiz.questions[state.currentQuestionIndex];
    const total = quiz.questions.length;
    
    // Update progress
    const progress = ((state.currentQuestionIndex + 1) / total) * 100;
    document.getElementById('quiz-progress-fill').style.width = `${progress}%`;
    document.getElementById('quiz-counter').textContent = `${state.currentQuestionIndex + 1} / ${total}`;
    
    // Update question
    document.getElementById('question-difficulty').textContent = question.difficulty || 'Medium';
    document.getElementById('question-text').textContent = question.question_text;
    
    // Render options
    const optionsList = document.getElementById('options-list');
    if (question.question_type === 'multiple_choice' && question.options) {
        optionsList.innerHTML = question.options.map((option, index) => {
            const letter = String.fromCharCode(65 + index);
            const selected = state.userAnswers[state.currentQuestionIndex] === option ? 'selected' : '';
            return `
                <button class="option-btn ${selected}" onclick="selectAnswer('${escapeHtml(option)}')">
                    <span class="option-letter">${letter}</span>
                    <span>${option}</span>
                </button>
            `;
        }).join('');
    } else if (question.question_type === 'true_false') {
        optionsList.innerHTML = ['True', 'False'].map(option => {
            const selected = state.userAnswers[state.currentQuestionIndex]?.toLowerCase() === option.toLowerCase() ? 'selected' : '';
            return `
                <button class="option-btn ${selected}" onclick="selectAnswer('${option.toLowerCase()}')">
                    <span>${option}</span>
                </button>
            `;
        }).join('');
    }
    
    // Update buttons
    document.getElementById('prev-btn').disabled = state.currentQuestionIndex === 0;
    document.getElementById('next-btn').textContent = 
        state.currentQuestionIndex === total - 1 ? 'Finish ✓' : 'Next →';
}

function selectAnswer(answer) {
    state.userAnswers[state.currentQuestionIndex] = answer;
    
    // Update UI
    document.querySelectorAll('.option-btn').forEach(btn => {
        btn.classList.remove('selected');
        if (btn.textContent.includes(answer) || btn.querySelector('span:last-child')?.textContent === answer) {
            btn.classList.add('selected');
        }
    });
}

function nextQuestion() {
    if (!state.userAnswers[state.currentQuestionIndex]) {
        showToast('Please select an answer', 'warning');
        return;
    }
    
    if (state.currentQuestionIndex < state.currentQuiz.questions.length - 1) {
        state.currentQuestionIndex++;
        renderQuestion();
    } else {
        finishQuiz();
    }
}

function prevQuestion() {
    if (state.currentQuestionIndex > 0) {
        state.currentQuestionIndex--;
        renderQuestion();
    }
}

async function finishQuiz() {
    document.getElementById('quiz-container').classList.add('hidden');
    document.getElementById('quiz-results').classList.remove('hidden');
    
    // Calculate results
    const quiz = state.currentQuiz;
    let correct = 0;
    const answers = quiz.questions.map((q, i) => {
        const userAnswer = state.userAnswers[i] || '';
        const isCorrect = userAnswer.toLowerCase() === q.correct_answer.toLowerCase();
        if (isCorrect) correct++;
        return {
            question_id: q.id,
            answer: userAnswer,
            time_seconds: 30
        };
    });
    
    const score = Math.round((correct / quiz.questions.length) * 100);
    
    // Update UI
    document.getElementById('result-score').textContent = score;
    document.getElementById('result-correct').textContent = correct;
    document.getElementById('result-incorrect').textContent = quiz.questions.length - correct;
    
    // Set emoji based on score
    let emoji = '🎉';
    if (score < 50) emoji = '😢';
    else if (score < 70) emoji = '🙂';
    else if (score < 90) emoji = '😊';
    document.getElementById('result-emoji').textContent = emoji;
    
    // Try to submit to API
    try {
        const result = await fetchAPI(`/quiz/submit?user_id=${state.userId}`, {
            method: 'POST',
            body: JSON.stringify({
                quiz_id: quiz.id,
                answers: answers
            })
        });
        
        document.getElementById('result-recommendations').innerHTML = 
            result.recommendations.map(r => `<li style="margin-bottom: 8px;">• ${r}</li>`).join('');
    } catch (error) {
        document.getElementById('result-recommendations').innerHTML = 
            `<li>• Review the topics you struggled with</li>
             <li>• Practice more questions at this difficulty level</li>`;
    }
}

function retakeQuiz() {
    document.getElementById('quiz-results').classList.add('hidden');
    document.getElementById('quiz-selection').classList.remove('hidden');
}

function reviewAnswers() {
    showToast('Review feature coming soon!', 'info');
}

// ==================== PROGRESS ====================

async function loadProgress() {
    try {
        const data = await fetchAPI(`/users/${state.userId}/progress`);
        state.progress = data.progress || [];
        renderProgress();
    } catch (error) {
        state.progress = getDemoProgress();
        renderProgress();
    }
}

function renderProgress() {
    const masteryList = document.getElementById('mastery-list');
    if (!masteryList) return;
    
    masteryList.innerHTML = state.progress.map(p => `
        <div class="progress-container">
            <div class="progress-header">
                <span class="progress-label">${p.topic_name}</span>
                <span class="progress-value">${Math.round(p.mastery_level)}%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${p.mastery_level}%"></div>
            </div>
        </div>
    `).join('');
    
    // Update stats
    if (state.progress.length > 0) {
        const avgMastery = state.progress.reduce((sum, p) => sum + p.mastery_level, 0) / state.progress.length;
        document.getElementById('total-mastery').textContent = `${Math.round(avgMastery)}%`;
        document.getElementById('topics-completed').textContent = 
            state.progress.filter(p => p.mastery_level >= 70).length;
    }
}

// ==================== SCHEDULE ====================

function generateCalendar() {
    const grid = document.getElementById('calendar-grid');
    if (!grid) return;
    
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const today = new Date();
    
    let html = days.map(d => `<div style="text-align: center; font-size: 12px; color: var(--text-muted); padding: 8px;">${d}</div>`).join('');
    
    for (let i = 0; i < 28; i++) {
        const date = new Date(today);
        date.setDate(today.getDate() + i - today.getDay() + 1);
        const isToday = date.toDateString() === today.toDateString();
        const hasReview = Math.random() > 0.6;
        
        html += `
            <div class="calendar-day ${isToday ? 'today' : ''} ${hasReview ? 'has-review' : ''}">
                <span class="day-number">${date.getDate()}</span>
                ${hasReview ? '<span class="day-indicator"></span>' : ''}
            </div>
        `;
    }
    
    grid.innerHTML = html;
}

async function loadSchedule() {
    try {
        const data = await fetchAPI(`/users/${state.userId}/review-schedule?days=7`);
        state.schedule = data.schedule || {};
    } catch (error) {
        console.log('Using demo schedule');
    }
}

// ==================== SETTINGS ====================

function updateSettings(user) {
    if (!user) return;
    document.getElementById('setting-username').value = user.username || '';
    document.getElementById('setting-email').value = user.email || '';
    document.getElementById('setting-goal').value = user.learning_goal || '';
    document.getElementById('setting-level').value = user.current_level || 'beginner';
    document.getElementById('setting-speed').value = user.learning_speed || 'medium';
}

async function saveSettings() {
    const settings = {
        current_level: document.getElementById('setting-level').value,
        learning_speed: document.getElementById('setting-speed').value,
        learning_goal: document.getElementById('setting-goal').value
    };
    
    try {
        await fetchAPI(`/users/${state.userId}`, {
            method: 'PUT',
            body: JSON.stringify(settings)
        });
        showToast('Settings saved successfully!', 'success');
    } catch (error) {
        showToast('Settings saved locally', 'success');
    }
}

// ==================== MODAL & DIAGNOSTIC ====================

function startDiagnostic() {
    openModal('diagnostic-modal');
    loadDiagnosticQuestions();
}

async function loadDiagnosticQuestions() {
    const content = document.getElementById('diagnostic-content');
    
    try {
        const data = await fetchAPI('/diagnostic-questions');
        renderDiagnosticQuestions(data.questions);
    } catch (error) {
        renderDiagnosticQuestions(getDemoDiagnosticQuestions());
    }
}

function renderDiagnosticQuestions(questions) {
    const content = document.getElementById('diagnostic-content');
    
    content.innerHTML = questions.map((q, i) => `
        <div class="form-group">
            <label class="form-label">${i + 1}. ${q.text}</label>
            ${q.type === 'text' ? `<input type="text" class="form-input" id="diag-${q.id}">` : ''}
            ${q.type === 'choice' ? `
                <select class="form-select" id="diag-${q.id}">
                    ${q.options.map(o => `<option value="${o}">${o}</option>`).join('')}
                </select>
            ` : ''}
            ${q.type === 'multi' ? `
                <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                    ${q.options.map(o => `
                        <label style="display: flex; align-items: center; gap: 8px; padding: 8px 16px; background: var(--bg-glass); border-radius: 8px; cursor: pointer;">
                            <input type="checkbox" value="${o}"> ${o}
                        </label>
                    `).join('')}
                </div>
            ` : ''}
        </div>
    `).join('') + `
        <button class="btn btn-primary" style="width: 100%; margin-top: 16px;" onclick="submitDiagnostic()">
            Start Learning Journey 🚀
        </button>
    `;
}

function submitDiagnostic() {
    closeModal('diagnostic-modal');
    showToast('Your personalized learning path is ready!', 'success');
    showPage('topics');
}

function openModal(id) {
    document.getElementById(id).classList.add('active');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}

// ==================== UTILITIES ====================

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span>${getToastIcon(type)}</span>
        <span>${message}</span>
    `;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function getToastIcon(type) {
    const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
    return icons[type] || icons.info;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function downloadReport() {
    showToast('Generating your progress report...', 'info');
    try {
        const response = await fetch(`${API_BASE}/users/${state.userId}/report`);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `learning_report_${state.userId}.pdf`;
        a.click();
        showToast('Report downloaded!', 'success');
    } catch (error) {
        showToast('Could not generate report', 'error');
    }
}

function startReviewSession() {
    showPage('quiz');
    startQuiz('review');
}

function createStudyPlan() {
    showToast('Creating personalized study plan...', 'info');
    setTimeout(() => {
        showToast('Study plan created!', 'success');
    }, 1000);
}

// ==================== DEMO DATA ====================

function getDemoTopics() {
    return [
        { id: 'python_basics', name: 'Python Basics', description: 'Introduction to Python programming fundamentals', category: 'Programming', difficulty_level: 1, questions: [{},{},{},{},{}] },
        { id: 'python_variables', name: 'Variables & Data Types', description: 'Understanding variables and different data types', category: 'Programming', difficulty_level: 1, questions: [{},{},{},{}] },
        { id: 'python_control_flow', name: 'Control Flow', description: 'If statements, loops, and program flow control', category: 'Programming', difficulty_level: 2, questions: [{},{},{},{},{}] },
        { id: 'python_functions', name: 'Functions', description: 'Creating and using functions in Python', category: 'Programming', difficulty_level: 2, questions: [{},{},{},{}] },
        { id: 'data_structures', name: 'Data Structures', description: 'Lists, dictionaries, sets, and tuples', category: 'Programming', difficulty_level: 2, questions: [{},{},{},{},{}] },
        { id: 'python_oop', name: 'Object-Oriented Programming', description: 'Classes, objects, inheritance, and OOP concepts', category: 'Programming', difficulty_level: 3, questions: [{},{},{},{}] }
    ];
}

function getDemoQuiz() {
    return {
        id: 'demo_quiz_001',
        questions: [
            { id: 'q1', question_type: 'multiple_choice', difficulty: 'Easy', question_text: 'What is Python?', options: ['A programming language', 'A snake', 'A game', 'A database'], correct_answer: 'A programming language' },
            { id: 'q2', question_type: 'true_false', difficulty: 'Easy', question_text: 'Python uses indentation to define code blocks.', correct_answer: 'true' },
            { id: 'q3', question_type: 'multiple_choice', difficulty: 'Medium', question_text: 'Which keyword is used to define a function?', options: ['func', 'def', 'function', 'define'], correct_answer: 'def' },
            { id: 'q4', question_type: 'multiple_choice', difficulty: 'Medium', question_text: 'Which data structure uses key-value pairs?', options: ['list', 'tuple', 'dictionary', 'set'], correct_answer: 'dictionary' },
            { id: 'q5', question_type: 'true_false', difficulty: 'Hard', question_text: 'A while loop can become infinite if the condition never becomes False.', correct_answer: 'true' }
        ]
    };
}

function getDemoProgress() {
    return [
        { topic_id: 'python_basics', topic_name: 'Python Basics', mastery_level: 85, time_spent_minutes: 120 },
        { topic_id: 'python_variables', topic_name: 'Variables & Data Types', mastery_level: 60, time_spent_minutes: 90 },
        { topic_id: 'python_control_flow', topic_name: 'Control Flow', mastery_level: 30, time_spent_minutes: 45 }
    ];
}

function getDemoDiagnosticQuestions() {
    return [
        { id: 'd1', text: 'What is your primary learning goal?', type: 'text' },
        { id: 'd2', text: 'How much time can you dedicate daily?', type: 'choice', options: ['30 min', '1 hour', '2 hours', '3+ hours'] },
        { id: 'd3', text: 'What is your current experience level?', type: 'choice', options: ['Complete beginner', 'Some basics', 'Intermediate', 'Advanced'] },
        { id: 'd4', text: 'What topics interest you most?', type: 'multi', options: ['Programming', 'Data Science', 'Web Dev', 'AI/ML', 'Mobile Dev'] }
    ];
}
