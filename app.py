from flask import Flask, request, jsonify, render_template, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.secret_key = 'replace_this_with_a_long_random_string_later' 
socketio = SocketIO(app)

def get_db_connection():
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    return conn

# ==========================================
# FRONT-END HTML ROUTES
# ==========================================
@app.route('/', methods=['GET'])
def home(): return render_template('index.html')

@app.route('/login', methods=['GET'])
def login_page(): return render_template('login.html')

@app.route('/profile')
def profile():
    if 'user_id' not in session: return redirect('/login')
    return render_template('profile.html', username=session['username'])

@app.route('/todo', methods=['GET'])
def todo_page():
    if 'user_id' not in session: return redirect('/login')
    return render_template('todo.html', username=session['username'])

@app.route('/blog', methods=['GET'])
def blog_page():
    if 'user_id' not in session: return redirect('/login')
    return render_template('blog.html', username=session['username'])

@app.route('/shop', methods=['GET'])
def shop_page():
    if 'user_id' not in session: return redirect('/login')
    return render_template('shop.html', username=session['username'])

@app.route('/cart', methods=['GET'])
def cart_page():
    if 'user_id' not in session: return redirect('/login')
    return render_template('cart.html', username=session['username'])

@app.route('/orders', methods=['GET'])
def orders_page():
    if 'user_id' not in session: return redirect('/login')
    return render_template('orders.html', username=session['username'])

@app.route('/chat', methods=['GET'])
def chat_page():
    if 'user_id' not in session: return redirect('/login')
    return render_template('chat.html', username=session['username'])
@app.route('/quiz', methods=['GET'])
def quiz_page():
    if 'user_id' not in session: return redirect('/login')
    return render_template('quiz.html', username=session['username'])

@app.route('/admin/quiz', methods=['GET'])
def admin_quiz_page():
    if 'user_id' not in session: return redirect('/login')
    return render_template('admin_quiz.html', username=session['username'])

# ==========================================
# TASK 1: AUTHENTICATION API
# ==========================================
@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json()
    if not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Missing fields"}), 400
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                     (data['username'], data['email'], generate_password_hash(data['password'])))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username/Email exists"}), 409
    finally:
        conn.close()
    return jsonify({"message": "Registered!"}), 201

@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json()
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (data.get('username'),)).fetchone()
    conn.close()
    if user and check_password_hash(user['password_hash'], data.get('password')):
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({"message": "Login successful!"}), 200
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/logout', methods=['POST'])
def logout_user():
    session.clear()
    return jsonify({"message": "Logged out"}), 200


# ==========================================
# TASK 2: TO-DO API
# ==========================================
@app.route('/api/tasks', methods=['GET', 'POST'])
def handle_tasks():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    conn = get_db_connection()
    if request.method == 'GET':
        tasks = conn.execute("SELECT * FROM tasks WHERE user_id = ?", (session['user_id'],)).fetchall()
        conn.close()
        return jsonify([{"id": r["id"], "task_name": r["task_name"], "is_completed": bool(r["is_completed"])} for r in tasks]), 200
    if request.method == 'POST':
        task_name = request.get_json().get('task_name')
        conn.execute("INSERT INTO tasks (user_id, task_name) VALUES (?, ?)", (session['user_id'], task_name))
        conn.commit()
        conn.close()
        return jsonify({"message": "Added"}), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT', 'DELETE'])
def update_delete_task(task_id):
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    conn = get_db_connection()
    if request.method == 'PUT':
        is_completed = request.get_json().get('is_completed')
        conn.execute("UPDATE tasks SET is_completed = ? WHERE id = ? AND user_id = ?", (is_completed, task_id, session['user_id']))
    if request.method == 'DELETE':
        conn.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({"message": "Success"}), 200


# ==========================================
# TASK 3: BLOG API
# ==========================================
@app.route('/api/posts', methods=['GET', 'POST'])
def handle_posts():
    conn = get_db_connection()
    if request.method == 'GET':
        posts = conn.execute("SELECT p.id, p.title, p.content, p.created_at, u.username FROM posts p JOIN users u ON p.user_id = u.id ORDER BY p.created_at DESC").fetchall()
        conn.close()
        return jsonify([dict(p) for p in posts]), 200
    if request.method == 'POST':
        if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
        data = request.get_json()
        conn.execute("INSERT INTO posts (user_id, title, content) VALUES (?, ?, ?)", (session['user_id'], data.get('title'), data.get('content')))
        conn.commit()
        conn.close()
        return jsonify({"message": "Post created"}), 201

@app.route('/api/posts/<int:post_id>/comments', methods=['GET', 'POST'])
def handle_comments(post_id):
    conn = get_db_connection()
    if request.method == 'GET':
        comments = conn.execute("SELECT c.id, c.content, c.created_at, u.username FROM comments c JOIN users u ON c.user_id = u.id WHERE c.post_id = ? ORDER BY c.created_at ASC", (post_id,)).fetchall()
        conn.close()
        return jsonify([dict(c) for c in comments]), 200
    if request.method == 'POST':
        if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
        conn.execute("INSERT INTO comments (user_id, post_id, content) VALUES (?, ?, ?)", (session['user_id'], post_id, request.get_json().get('content')))
        conn.commit()
        conn.close()
        return jsonify({"message": "Comment added"}), 201


# ==========================================
# TASK 4: E-COMMERCE API
# ==========================================
@app.route('/api/products', methods=['GET'])
def get_products():
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return jsonify([dict(row) for row in products]), 200

@app.route('/api/cart', methods=['GET', 'POST'])
def manage_cart():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    conn = get_db_connection()
    if request.method == 'GET':
        items = conn.execute("SELECT c.id as cart_id, p.id as product_id, p.name, p.price, c.quantity FROM cart_items c JOIN products p ON c.product_id = p.id WHERE c.user_id = ?", (session['user_id'],)).fetchall()
        conn.close()
        return jsonify([dict(row) for row in items]), 200
    if request.method == 'POST':
        product_id = request.get_json().get('product_id')
        existing = conn.execute("SELECT id FROM cart_items WHERE user_id = ? AND product_id = ?", (session['user_id'], product_id)).fetchone()
        if existing:
            conn.execute("UPDATE cart_items SET quantity = quantity + 1 WHERE id = ?", (existing['id'],))
        else:
            conn.execute("INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, 1)", (session['user_id'], product_id))
        conn.commit()
        conn.close()
        return jsonify({"message": "Added"}), 200

@app.route('/api/cart/<int:cart_id>', methods=['DELETE'])
def remove_from_cart(cart_id):
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    conn = get_db_connection()
    conn.execute("DELETE FROM cart_items WHERE id = ? AND user_id = ?", (cart_id, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({"message": "Removed"}), 200

@app.route('/api/checkout', methods=['POST'])
def checkout():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    address = request.get_json().get('shipping_address')
    if not address: return jsonify({"error": "Address required"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cart_items = cursor.execute("SELECT c.product_id, c.quantity, p.price FROM cart_items c JOIN products p ON c.product_id = p.id WHERE c.user_id = ?", (session['user_id'],)).fetchall()
    if not cart_items: return jsonify({"error": "Cart empty"}), 400
    
    total = sum(i['price'] * i['quantity'] for i in cart_items)
    cursor.execute("INSERT INTO orders (user_id, total_price, shipping_address) VALUES (?, ?, ?)", (session['user_id'], total, address))
    order_id = cursor.lastrowid
    
    for i in cart_items:
        cursor.execute("INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase) VALUES (?, ?, ?, ?)", (order_id, i['product_id'], i['quantity'], i['price']))
    
    cursor.execute("DELETE FROM cart_items WHERE user_id = ?", (session['user_id'],))
    conn.commit()
    conn.close()
    return jsonify({"message": "Success", "order_id": order_id}), 200

@app.route('/api/orders', methods=['GET'])
def get_orders():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    conn = get_db_connection()
    orders = conn.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (session['user_id'],)).fetchall()
    order_list = []
    for order in orders:
        items = conn.execute("SELECT p.name, p.image_url, o.quantity, o.price_at_purchase FROM order_items o JOIN products p ON o.product_id = p.id WHERE o.order_id = ?", (order['id'],)).fetchall()
        order_list.append({
            "id": order['id'], "total_price": order['total_price'], "status": order['status'], 
            "created_at": order['created_at'], "shipping_address": order['shipping_address'], 
            "items": [dict(i) for i in items]
        })
    conn.close()
    return jsonify(order_list), 200

# ==========================================
# TASK 5: REAL-TIME CHAT API & SOCKETS
# ==========================================
@app.route('/api/messages', methods=['GET'])
def get_chat_history():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    conn = get_db_connection()
    messages = conn.execute("SELECT m.content, m.timestamp, u.username FROM messages m JOIN users u ON m.user_id = u.id ORDER BY m.timestamp ASC LIMIT 50").fetchall()
    conn.close()
    return jsonify([dict(m) for m in messages]), 200

@socketio.on('send_message')
def handle_message(data):
    if 'user_id' not in session: return False
    content = data.get('message')
    if not content: return False

    conn = get_db_connection()
    conn.execute("INSERT INTO messages (user_id, content) VALUES (?, ?)", (session['user_id'], content))
    conn.commit()
    conn.close()

    emit('receive_message', {'username': session['username'], 'message': content}, broadcast=True)

# ==========================================
# TASK 6: QUIZ API
# ==========================================
@app.route('/api/questions', methods=['GET', 'POST'])
def handle_questions():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    conn = get_db_connection()
    if request.method == 'GET':
        # Notice we do NOT select 'correct_option'. The frontend shouldn't know it.
        questions = conn.execute("SELECT id, question_text, option_a, option_b, option_c, option_d FROM questions").fetchall()
        conn.close()
        return jsonify([dict(q) for q in questions]), 200
    
    if request.method == 'POST':
        data = request.get_json()
        conn.execute("INSERT INTO questions (question_text, option_a, option_b, option_c, option_d, correct_option) VALUES (?, ?, ?, ?, ?, ?)",
                     (data['question_text'], data['option_a'], data['option_b'], data['option_c'], data['option_d'], data['correct_option']))
        conn.commit()
        conn.close()
        return jsonify({"message": "Question added"}), 201

@app.route('/api/quiz/submit', methods=['POST'])
def submit_quiz():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    answers = request.get_json().get('answers', {})
    if not answers: return jsonify({"error": "No answers provided"}), 400

    conn = get_db_connection()
    questions = conn.execute("SELECT id, correct_option FROM questions").fetchall()
    
    score = 0
    feedback = []
    
    # Grading happens purely on the backend
    for q in questions:
        qid = str(q['id'])
        user_ans = answers.get(qid)
        is_correct = (user_ans == q['correct_option'])
        if is_correct: score += 1
        feedback.append({"question_id": q['id'], "user_answer": user_ans, "correct_answer": q['correct_option'], "is_correct": is_correct})
        
    total = len(questions)
    conn.execute("INSERT INTO quiz_scores (user_id, score, total) VALUES (?, ?, ?)", (session['user_id'], score, total))
    conn.commit()
    conn.close()
    
    return jsonify({"score": score, "total": total, "feedback": feedback}), 200

@app.route('/api/scores', methods=['GET'])
def get_scores():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    conn = get_db_connection()
    scores = conn.execute("SELECT score, total, created_at FROM quiz_scores WHERE user_id = ? ORDER BY created_at DESC", (session['user_id'],)).fetchall()
    conn.close()
    return jsonify([dict(s) for s in scores]), 200
if __name__ == '__main__':
    # Notice we are running socketio.run, NOT app.run
    socketio.run(app, debug=True, port=5000)