from flask import Flask, request, render_template, session, redirect, url_for, flash
import datetime
import json
import pytz
from decouple import config
tz_tehran = pytz.timezone('Asia/Tehran')


class Question:
    def __init__(self, question_id, title, answer, choices):
        self.question_id, self.title, self.answer, self.choices = question_id, title, answer, choices


class User:
    def __init__(self, name, studentnumber, score):
        self.name, self.studentnumber, self.score = name, studentnumber, score


with open('static/questions.json', 'r', encoding='utf-8') as file:
    questions = json.loads(file.read())
admin_usename = config('ADMIN_USERNAME')
admin_studentnumner = config('ADMIN_STUDENTNUMBER')

scoreboard_user = []
flag = 1
start_time, end_time = '', ''
app = Flask(__name__)
app.secret_key = config('SECRET_KEY')


@app.route('/')
def index():
    global questions
    time_now = datetime.datetime.now(tz_tehran).time().strftime("%H:%M")
    if time_now > end_time:
        return render_template('time.html', message="زمان شرکت در مسابقه تمام شده است.")
    if time_now < start_time:
        return render_template('time.html', message="مسابقه در ساعت زیر شروع می شود", time=start_time)
    if 'name' in session:
        q = []
        for question in questions:
            if str(question['question_id']) not in session['answered']:
                q.append(Question(question['question_id'], question['title'], question['answer'],
                                  question['choices']))
        if len(q) == 0:
            return redirect('live_scoreboard')
        return render_template('quiz.html', questions=q)
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    global scoreboard_user
    is_exits = False
    if request.method == 'POST':
        name = request.form.get('name')
        studentnumber = request.form.get('studentnumber')
        time_now = datetime.datetime.now(tz_tehran).time().strftime("%H:%M")
        if name != admin_username and studentnumber != admin_studentnumber:
            if time_now > end_time:
                return redirect(url_for('index'))
            if time_now < start_time:
                return redirect(url_for('index'))
        for user in scoreboard_user:
            if user.studentnumber == request.form.get('studentnumber'):
                is_exits = True
        if not is_exits:
            session['name'] = name
            session['studentnumber'] = studentnumber
            session['score'] = 0
            session['answered'] = ''
            if session['name'] == admin_username and session['studentnumber'] == admin_studentnumber:
                return redirect(url_for('dashboard'))
            else:
                scoreboard_user.append(User(session['name'], session['studentnumber'], session['score']))
                return redirect(url_for('index'))
        if is_exits:
            flash('این شماره دانشجویی در مسابقه شرکت کرده است.')
    return render_template('index.html')


@app.route('/check_answer', methods=['POST'])
def check_answer():
    if request.method == 'POST':
        question_id = int(request.form.get('question_id'))
        choice = request.form.get('choice')
        if str(question_id) not in session['answered']:
            if session['name'] != admin_username and session['studentnumber'] != admin_studentnumber:
                session['answered'] += str(question_id)
                for question in questions:
                    if question['question_id'] == question_id and question['correct'] == choice:
                        for user in scoreboard_user:
                            if user.studentnumber == session['studentnumber']:
                                user.score += 10
                                break
                        break
    return ''


@app.route('/scoreboard')
def scoreboard():
    global scoreboard_user
    scoreboard_user = sorted(scoreboard_user, key=lambda user: user.score, reverse=True)
    return render_template('scoreboard.html', scoreboard=scoreboard_user)


@app.route('/live_scoreboard')
def live_scoreboard():
    return render_template('live_scoreboard.html')


@app.route('/dashboard')
def dashboard():
    if 'name' in session:
        return render_template('dashboard.html')
    else:
        return redirect(url_for('login'))


@app.route('/set_time', methods=['POST'])
def ser_time():
    global start_time, end_time
    if 'name' in session:
        if request.method == 'POST':
            start_hour = int(request.form.get('start-hour'))
            start_minute = int(request.form.get('start-minute'))
            end_hour = int(request.form.get('end-hour'))
            end_minute = int(request.form.get('end-minute'))
            start_time = datetime.time(start_hour, start_minute).strftime("%H:%M")
            end_time = datetime.time(end_hour, end_minute).strftime("%H:%M")
            session.pop('name')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run()
