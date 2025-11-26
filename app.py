from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, send_file
)
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from models import (
    register_user, validate_user,
    save_document, get_user_documents, get_document_by_id
)
from processor import (
    ingest_documents, preprocess_text_func,
    extract_insights, summarize_text_func
)

# -------------------------
# Flask App Configuration
# -------------------------
app = Flask(__name__)
app.secret_key = "secret123"
app.config["UPLOAD_FOLDER"] = "uploads"

# Create uploads folder if not exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# -------------------------
# Routes
# -------------------------

@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# -------- Register --------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        try:
            register_user(username, password)
            return redirect(url_for("login"))
        except Exception as e:
            return f"Error: {e}"
    return render_template("register.html")


# -------- Login --------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if validate_user(username, password):
            session["username"] = username
            return redirect(url_for("upload_file"))
        else:
            return "Invalid username or password"
    return render_template("login.html")


# -------- Upload --------
@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        if "file" not in request.files:
            return "No file uploaded", 400

        file = request.files["file"]
        if file.filename == "":
            return "No selected file", 400

        # Secure the filename
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        # Save uploaded file
        file.save(filepath)

        # Process text
        raw_text = ingest_documents(filepath)
        preprocessed = preprocess_text_func(raw_text)
        insights = extract_insights(preprocessed)
        summary = summarize_text_func(preprocessed)

        # Save to MongoDB
        save_document(
            session["username"],
            filename,
            filepath,
            raw_text,
            preprocessed,
            summary,
            insights
        )

        # Redirect to results page
        return redirect(url_for("results", filename=filename))

    return render_template("upload.html")


# -------- Results Page --------
@app.route("/results/<filename>")
def results(filename):
    if "username" not in session:
        return redirect(url_for("login"))

    docs = get_user_documents(session["username"])
    doc = next((d for d in docs if d["filename"] == filename), None)
    if not doc:
        return "Document not found", 404

    return render_template("results.html", document=doc)


# -------- Dashboard --------
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))
    docs = get_user_documents(session["username"])
    return render_template("dashboard.html", docs=docs, username=session["username"])


# -------- API: Dashboard Metrics --------
@app.route("/api/metrics")
def api_metrics():
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    docs = get_user_documents(session["username"])

    # Daily uploads (last 7 days)
    today = datetime.now().date()
    daily_counts = []
    for i in range(7):
        day = today - timedelta(days=6 - i)
        count = sum(1 for d in docs if datetime.fromisoformat(d["created_at"]).date() == day)
        daily_counts.append({"day": day.strftime("%b %d"), "count": count})

    # Entity frequency
    entity_freq = {}
    for d in docs:
        if d.get("insights") and d["insights"].get("entities"):
            for ent, label in d["insights"]["entities"]:
                entity_freq[label] = entity_freq.get(label, 0) + 1

    return jsonify({"daily": daily_counts, "entities": entity_freq})


# -------- Download File --------
@app.route("/download/<doc_id>")
def download_file(doc_id):
    if "username" not in session:
        return redirect(url_for("login"))

    doc = get_document_by_id(doc_id)
    if not doc or doc["username"] != session["username"]:
        return "File not found or unauthorized", 404

    return send_file(doc["filepath"], as_attachment=True)


# -------- View Document --------
@app.route("/document/<doc_id>")
def view_document(doc_id):
    if "username" not in session:
        return redirect(url_for("login"))

    doc = get_document_by_id(doc_id)
    if not doc or doc["username"] != session["username"]:
        return "Document not found", 404

    return render_template("results.html", document=doc)


# -------- Logout --------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# -------------------------
# Run the app
# -------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)