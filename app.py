from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

# --- Flask & DB 設定 ---
app = Flask(__name__)
app.secret_key = "change-me"  # 本番では環境変数で

BASE_DIR = Path(__file__).resolve().parent
db_path = BASE_DIR / "tasks.sqlite3"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# --- モデル ---
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    done = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Task {self.id}:{self.title[:10]}>"

# 初回起動時にテーブル作成
with app.app_context():
    db.create_all()

# --- ルーティング ---
@app.get("/")
def index():
    q = request.args.get("q", "").strip()
    show = request.args.get("show", "all")  # all|open|done
    query = Task.query
    if q:
        query = query.filter(Task.title.contains(q))
    if show == "open":
        query = query.filter_by(done=False)
    elif show == "done":
        query = query.filter_by(done=True)
    tasks = query.order_by(Task.created_at.desc()).all()
    open_count = Task.query.filter_by(done=False).count()
    done_count = Task.query.filter_by(done=True).count()
    return render_template("index.html",
                           tasks=tasks, q=q, show=show,
                           open_count=open_count, done_count=done_count)

@app.post("/task")
def create_task():
    title = request.form.get("title", "").strip()
    if not title:
        flash("タイトルを入力してください。", "warn")
        return redirect(url_for("index"))
    t = Task(title=title)
    db.session.add(t)
    db.session.commit()
    flash("タスクを追加しました。", "ok")
    return redirect(url_for("index"))

@app.post("/task/<int:task_id>/toggle")
def toggle_task(task_id):
    t = Task.query.get_or_404(task_id)
    t.done = not t.done
    db.session.commit()
    return redirect(url_for("index"))

@app.post("/task/<int:task_id>/delete")
def delete_task(task_id):
    t = Task.query.get_or_404(task_id)
    db.session.delete(t)
    db.session.commit()
    flash("タスクを削除しました。", "ok")
    return redirect(url_for("index"))

if __name__ == "__main__":
    # ローカル開発用: python app.py
    app.run(host="0.0.0.0", port=5000, debug=True)
