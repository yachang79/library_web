from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from datetime import date

app = Flask(__name__)
app.secret_key = 'library_secret_key_2024'

DB_PATH = os.path.join(os.path.dirname(__file__), 'library.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            member_id TEXT NOT NULL UNIQUE,
            address TEXT,
            phone TEXT,
            created_at TEXT DEFAULT (date('now'))
        );

        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            serial_no TEXT NOT NULL UNIQUE,
            author TEXT,
            publish_date TEXT,
            created_at TEXT DEFAULT (date('now'))
        );

        CREATE TABLE IF NOT EXISTS borrowings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            borrow_date TEXT NOT NULL,
            return_date TEXT,
            status TEXT DEFAULT 'borrowed',
            FOREIGN KEY (member_id) REFERENCES members(id),
            FOREIGN KEY (book_id) REFERENCES books(id)
        );
    ''')
    conn.commit()
    conn.close()


# ── 首頁 ──────────────────────────────────────────────
@app.route('/')
def index():
    conn = get_db()
    stats = {
        'members': conn.execute('SELECT COUNT(*) FROM members').fetchone()[0],
        'books': conn.execute('SELECT COUNT(*) FROM books').fetchone()[0],
        'borrowed': conn.execute("SELECT COUNT(*) FROM borrowings WHERE status='borrowed'").fetchone()[0],
    }
    recent = conn.execute('''
        SELECT b.title, m.name, br.borrow_date
        FROM borrowings br
        JOIN members m ON br.member_id = m.id
        JOIN books b ON br.book_id = b.id
        WHERE br.status = 'borrowed'
        ORDER BY br.borrow_date DESC LIMIT 5
    ''').fetchall()
    conn.close()
    return render_template('index.html', stats=stats, recent=recent)


@app.route('/healthz')
def healthz():
    return {'status': 'ok'}, 200


# ── 會員管理 ──────────────────────────────────────────
@app.route('/members')
def members():
    q = request.args.get('q', '')
    conn = get_db()
    if q:
        rows = conn.execute(
            "SELECT * FROM members WHERE name LIKE ? OR member_id LIKE ? OR phone LIKE ? ORDER BY id DESC",
            (f'%{q}%', f'%{q}%', f'%{q}%')
        ).fetchall()
    else:
        rows = conn.execute('SELECT * FROM members ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('members/list.html', members=rows, q=q)


@app.route('/members/new', methods=['GET', 'POST'])
def member_new():
    if request.method == 'POST':
        name = request.form['name'].strip()
        member_id = request.form['member_id'].strip()
        address = request.form['address'].strip()
        phone = request.form['phone'].strip()
        if not name or not member_id:
            flash('姓名與會員編號為必填欄位', 'danger')
            return render_template('members/form.html', action='new', form=request.form)
        conn = get_db()
        try:
            conn.execute(
                'INSERT INTO members (name, member_id, address, phone) VALUES (?, ?, ?, ?)',
                (name, member_id, address, phone)
            )
            conn.commit()
            flash('會員新增成功', 'success')
            return redirect(url_for('members'))
        except sqlite3.IntegrityError:
            flash('會員編號已存在', 'danger')
            return render_template('members/form.html', action='new', form=request.form)
        finally:
            conn.close()
    return render_template('members/form.html', action='new', form={})


@app.route('/members/<int:mid>/edit', methods=['GET', 'POST'])
def member_edit(mid):
    conn = get_db()
    member = conn.execute('SELECT * FROM members WHERE id=?', (mid,)).fetchone()
    if not member:
        conn.close()
        flash('找不到該會員', 'danger')
        return redirect(url_for('members'))
    if request.method == 'POST':
        name = request.form['name'].strip()
        member_id = request.form['member_id'].strip()
        address = request.form['address'].strip()
        phone = request.form['phone'].strip()
        if not name or not member_id:
            flash('姓名與會員編號為必填欄位', 'danger')
            conn.close()
            return render_template('members/form.html', action='edit', form=request.form, member=member)
        try:
            conn.execute(
                'UPDATE members SET name=?, member_id=?, address=?, phone=? WHERE id=?',
                (name, member_id, address, phone, mid)
            )
            conn.commit()
            flash('會員資料更新成功', 'success')
            return redirect(url_for('members'))
        except sqlite3.IntegrityError:
            flash('會員編號已存在', 'danger')
            return render_template('members/form.html', action='edit', form=request.form, member=member)
        finally:
            conn.close()
    conn.close()
    return render_template('members/form.html', action='edit', form=member, member=member)


@app.route('/members/<int:mid>/delete', methods=['POST'])
def member_delete(mid):
    conn = get_db()
    borrowed = conn.execute(
        "SELECT COUNT(*) FROM borrowings WHERE member_id=? AND status='borrowed'", (mid,)
    ).fetchone()[0]
    if borrowed:
        flash('該會員仍有未歸還書籍，無法刪除', 'danger')
    else:
        conn.execute('DELETE FROM members WHERE id=?', (mid,))
        conn.commit()
        flash('會員已刪除', 'success')
    conn.close()
    return redirect(url_for('members'))


# ── 圖書管理 ──────────────────────────────────────────
@app.route('/books')
def books():
    q = request.args.get('q', '')
    conn = get_db()
    if q:
        rows = conn.execute(
            "SELECT * FROM books WHERE title LIKE ? OR serial_no LIKE ? OR author LIKE ? ORDER BY id DESC",
            (f'%{q}%', f'%{q}%', f'%{q}%')
        ).fetchall()
    else:
        rows = conn.execute('SELECT * FROM books ORDER BY id DESC').fetchall()
    # 標示每本書的借閱狀態
    book_list = []
    for book in rows:
        is_borrowed = conn.execute(
            "SELECT COUNT(*) FROM borrowings WHERE book_id=? AND status='borrowed'", (book['id'],)
        ).fetchone()[0]
        book_list.append({'book': book, 'is_borrowed': bool(is_borrowed)})
    conn.close()
    return render_template('books/list.html', book_list=book_list, q=q)


@app.route('/books/new', methods=['GET', 'POST'])
def book_new():
    if request.method == 'POST':
        title = request.form['title'].strip()
        serial_no = request.form['serial_no'].strip()
        author = request.form['author'].strip()
        publish_date = request.form['publish_date'].strip()
        if not title or not serial_no:
            flash('書名與流水號為必填欄位', 'danger')
            return render_template('books/form.html', action='new', form=request.form)
        conn = get_db()
        try:
            conn.execute(
                'INSERT INTO books (title, serial_no, author, publish_date) VALUES (?, ?, ?, ?)',
                (title, serial_no, author, publish_date)
            )
            conn.commit()
            flash('圖書新增成功', 'success')
            return redirect(url_for('books'))
        except sqlite3.IntegrityError:
            flash('流水號已存在', 'danger')
            return render_template('books/form.html', action='new', form=request.form)
        finally:
            conn.close()
    return render_template('books/form.html', action='new', form={})


@app.route('/books/<int:bid>/edit', methods=['GET', 'POST'])
def book_edit(bid):
    conn = get_db()
    book = conn.execute('SELECT * FROM books WHERE id=?', (bid,)).fetchone()
    if not book:
        conn.close()
        flash('找不到該書籍', 'danger')
        return redirect(url_for('books'))
    if request.method == 'POST':
        title = request.form['title'].strip()
        serial_no = request.form['serial_no'].strip()
        author = request.form['author'].strip()
        publish_date = request.form['publish_date'].strip()
        if not title or not serial_no:
            flash('書名與流水號為必填欄位', 'danger')
            conn.close()
            return render_template('books/form.html', action='edit', form=request.form, book=book)
        try:
            conn.execute(
                'UPDATE books SET title=?, serial_no=?, author=?, publish_date=? WHERE id=?',
                (title, serial_no, author, publish_date, bid)
            )
            conn.commit()
            flash('圖書資料更新成功', 'success')
            return redirect(url_for('books'))
        except sqlite3.IntegrityError:
            flash('流水號已存在', 'danger')
            return render_template('books/form.html', action='edit', form=request.form, book=book)
        finally:
            conn.close()
    conn.close()
    return render_template('books/form.html', action='edit', form=book, book=book)


@app.route('/books/<int:bid>/delete', methods=['POST'])
def book_delete(bid):
    conn = get_db()
    borrowed = conn.execute(
        "SELECT COUNT(*) FROM borrowings WHERE book_id=? AND status='borrowed'", (bid,)
    ).fetchone()[0]
    if borrowed:
        flash('該書籍目前借出中，無法刪除', 'danger')
    else:
        conn.execute('DELETE FROM books WHERE id=?', (bid,))
        conn.commit()
        flash('書籍已刪除', 'success')
    conn.close()
    return redirect(url_for('books'))


# ── 借閱管理 ──────────────────────────────────────────
@app.route('/borrowings')
def borrowings():
    status_filter = request.args.get('status', 'borrowed')
    conn = get_db()
    rows = conn.execute('''
        SELECT br.id, m.name AS member_name, m.member_id AS member_code,
               b.title AS book_title, b.serial_no,
               br.borrow_date, br.return_date, br.status
        FROM borrowings br
        JOIN members m ON br.member_id = m.id
        JOIN books b ON br.book_id = b.id
        WHERE br.status = ?
        ORDER BY br.borrow_date DESC
    ''', (status_filter,)).fetchall()
    conn.close()
    return render_template('borrowings/list.html', borrowings=rows, status_filter=status_filter)


@app.route('/borrowings/new', methods=['GET', 'POST'])
def borrowing_new():
    conn = get_db()
    if request.method == 'POST':
        member_id = request.form['member_id']
        book_id = request.form['book_id']
        borrow_date = request.form['borrow_date']
        already = conn.execute(
            "SELECT COUNT(*) FROM borrowings WHERE book_id=? AND status='borrowed'", (book_id,)
        ).fetchone()[0]
        if already:
            flash('該書籍目前已借出', 'danger')
        else:
            conn.execute(
                "INSERT INTO borrowings (member_id, book_id, borrow_date, status) VALUES (?, ?, ?, 'borrowed')",
                (member_id, book_id, borrow_date)
            )
            conn.commit()
            flash('借閱登記成功', 'success')
            conn.close()
            return redirect(url_for('borrowings'))

    members = conn.execute('SELECT id, name, member_id FROM members ORDER BY name').fetchall()
    available_books = conn.execute('''
        SELECT b.id, b.title, b.serial_no FROM books b
        WHERE b.id NOT IN (
            SELECT book_id FROM borrowings WHERE status='borrowed'
        )
        ORDER BY b.title
    ''').fetchall()
    conn.close()
    return render_template('borrowings/form.html',
                           members=members,
                           available_books=available_books,
                           today=date.today().isoformat())


@app.route('/borrowings/<int:brid>/return', methods=['POST'])
def borrowing_return(brid):
    return_date = date.today().isoformat()
    conn = get_db()
    conn.execute(
        "UPDATE borrowings SET status='returned', return_date=? WHERE id=?",
        (return_date, brid)
    )
    conn.commit()
    conn.close()
    flash('歸還登記成功', 'success')
    return redirect(url_for('borrowings'))


init_db()

if __name__ == '__main__':
    app.run(debug=True)
