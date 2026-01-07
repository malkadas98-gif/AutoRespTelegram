# app.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# --- إعداد التطبيق ---
app = Flask(__name__)

# تحديد مسار قاعدة البيانات في المسار الرئيسي للتطبيق
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "flight_bot.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# --- إنشاء SQLAlchemy ---
db = SQLAlchemy(app)

# --- تعريف نموذج (مثال جدول للمسافر) ---
class Passenger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

# --- دالة تهيئة قاعدة البيانات ---
def init_db():
    if not os.path.exists(DB_PATH):
        db.create_all()
        print(f"🗄️ تم إنشاء قاعدة البيانات في: {DB_PATH}")
    else:
        print(f"🗄️ قاعدة البيانات موجودة مسبقاً في: {DB_PATH}")

# --- مثال لإضافة بيانات أولية ---
def add_initial_data():
    if Passenger.query.count() == 0:
        p1 = Passenger(name="Ali", email="ali@example.com")
        p2 = Passenger(name="Sara", email="sara@example.com")
        db.session.add_all([p1, p2])
        db.session.commit()
        print("✅ تم إضافة بيانات أولية للجدول Passenger")

# --- مسار رئيسي لاختبار التطبيق ---
@app.route("/")
def index():
    passengers = Passenger.query.all()
    return "<br>".join([f"{p.id}: {p.name} ({p.email})" for p in passengers])

# --- نقطة البداية ---
if __name__ == "__main__":
    init_db()
    add_initial_data()
    app.run(host="0.0.0.0", port=5000, debug=True)
