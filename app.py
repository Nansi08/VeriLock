import json
import hashlib
import os
from flask import Flask, render_template, request, redirect, flash, url_for, session
from werkzeug.utils import secure_filename
from web3 import Web3

app = Flask(__name__)
app.secret_key = "dev-secret-key"

# -------------------------------------------------
# 🔧 Configuration
# -------------------------------------------------
GANACHE_URL = "http://127.0.0.1:8545"
CONTRACT_DATA_FILE = "contract_data.json"

# Folder to save uploaded documents
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Folder to store user data (simple JSON)
DATA_FOLDER = os.path.join(os.getcwd(), "data")
os.makedirs(DATA_FOLDER, exist_ok=True)
STUDENT_FILE = os.path.join(DATA_FOLDER, "students.json")
FACULTY_FILE = os.path.join(DATA_FOLDER, "faculty.json")
COMPANY_FILE = os.path.join(DATA_FOLDER, "companies.json")

for f in [STUDENT_FILE, FACULTY_FILE, COMPANY_FILE]:
    if not os.path.exists(f):
        with open(f, "w") as file:
            json.dump({}, file)

# -------------------------------------------------
# 🌐 Blockchain Connection
# -------------------------------------------------
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
if not w3.is_connected():
    raise RuntimeError(f"Cannot connect to Ganache at {GANACHE_URL}")

if not os.path.exists(CONTRACT_DATA_FILE):
    raise RuntimeError(f"{CONTRACT_DATA_FILE} not found. Please deploy contract first.")

with open(CONTRACT_DATA_FILE, "r") as f:
    data = json.load(f)

abi = data.get("abi")
contract_address = data.get("address")

if not abi or not contract_address:
    raise RuntimeError("contract_data.json must contain 'abi' and 'address' fields.")

contract = w3.eth.contract(address=w3.to_checksum_address(contract_address), abi=abi)

if len(w3.eth.accounts) == 0:
    raise RuntimeError("No accounts available in Ganache.")
w3.eth.default_account = w3.eth.accounts[0]

# -------------------------------------------------
# 🔐 Helper Functions
# -------------------------------------------------
def compute_sha256(file_stream) -> str:
    file_stream.seek(0)
    sha = hashlib.sha256()
    for chunk in iter(lambda: file_stream.read(4096), b""):
        sha.update(chunk)
    file_stream.seek(0)
    return sha.hexdigest()

def load_users(role):
    file_map = {
        "student": STUDENT_FILE,
        "faculty": FACULTY_FILE,
        "company": COMPANY_FILE,
    }
    with open(file_map[role], "r") as f:
        return json.load(f)

def save_users(role, data):
    file_map = {
        "student": STUDENT_FILE,
        "faculty": FACULTY_FILE,
        "company": COMPANY_FILE,
    }
    with open(file_map[role], "w") as f:
        json.dump(data, f, indent=4)

# -------------------------------------------------
# 🏠 Home
# -------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

# -------------------------------------------------
# 📁 Upload
# -------------------------------------------------
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "GET":
        return render_template("upload.html")

    uploaded = request.files.get("file")
    if not uploaded or uploaded.filename == "":
        flash("No file selected.", "danger")
        return redirect(url_for("upload"))

    filename = secure_filename(uploaded.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    uploaded.save(filepath)

    with open(filepath, "rb") as f:
        doc_hash = compute_sha256(f)

    try:
        tx_hash = contract.functions.uploadDocument(doc_hash).transact()
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    except Exception as e:
        flash(f"Error uploading to blockchain: {e}", "danger")
        return redirect(url_for("upload"))

    return render_template(
        "upload_result.html",
        filename=filename,
        doc_hash=doc_hash,
        tx_hash=tx_hash.hex(),
        tx_block=receipt.blockNumber,
    )

# -------------------------------------------------
# 🔍 Verify
# -------------------------------------------------
@app.route("/verify", methods=["GET", "POST"])
def verify():
    if request.method == "GET":
        return render_template("verify.html", verified=None, doc_hash=None)

    uploaded = request.files.get("file")
    input_hash = request.form.get("doc_hash", "").strip()

    if uploaded and uploaded.filename != "":
        doc_hash = compute_sha256(uploaded.stream)
    elif input_hash:
        doc_hash = input_hash
    else:
        flash("Please upload a file or enter a document hash.", "warning")
        return redirect(url_for("verify"))

    try:
        tx_hash = contract.functions.verifyDocument(doc_hash).transact()
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        verified = contract.functions.verifyDocument(doc_hash).call()
    except Exception as e:
        flash(f"Error checking contract: {e}", "danger")
        return redirect(url_for("verify"))

    return render_template("verify.html", verified=verified, doc_hash=doc_hash)

# -------------------------------------------------
# 👤 Login + Signup Routes (Student / Faculty / Company)
# -------------------------------------------------
@app.route("/login/<role>", methods=["GET", "POST"])
def login(role):
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        users = load_users(role)

        if email in users and users[email]["password"] == password:
            session["user"] = email
            flash("Login successful!", "success")

            # ✅ Redirect based on role
            if role == "student":
                return redirect(url_for("upload"))  # Student → Upload page
            elif role == "faculty":
                return redirect(url_for("faculty_dashboard"))
            elif role == "company":
                return redirect(url_for("company_dashboard"))
            else:
                return redirect(url_for("index"))
        else:
            flash("Invalid credentials. Try again.", "danger")

    return render_template(f"login_{role}.html")

@app.route("/signup/<role>", methods=["GET", "POST"])
def signup(role):
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        users = load_users(role)

        if email in users:
            flash("Account already exists. Please log in.", "warning")
            return redirect(url_for("login", role=role))

        users[email] = {"name": name, "password": password}
        save_users(role, users)

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("login", role=role))

    return render_template(f"signup_{role}.html")

# -------------------------------------------------
# 🧭 Dashboards
# -------------------------------------------------
@app.route("/student/dashboard")
def student_dashboard():
    return render_template("student_dashboard.html")

@app.route("/faculty/dashboard")
def faculty_dashboard():
    return render_template("faculty_dashboard.html")

@app.route("/company/dashboard")
def company_dashboard():
    return render_template("company_dashboard.html")

# -------------------------------------------------
# 🧩 About & Features Pages
# -------------------------------------------------
@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/features")
def features():
    return render_template("features.html")

# -------------------------------------------------
# 🚀 Run App
# -------------------------------------------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
