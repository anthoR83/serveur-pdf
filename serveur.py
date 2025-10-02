from flask import Flask, request, jsonify, send_file, send_from_directory
import sqlite3, os
from datetime import datetime, date
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO

app = Flask(__name__)

DB_PATH = "app.db"
PDF_DIR = "pdfs"
REMPLIS_DIR = "remplis"

os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(REMPLIS_DIR, exist_ok=True)

@app.route("/mobile")
def mobile_home():
    return send_from_directory(".", "index.html")  # si index.html est à la racine du projet


# ---------------- FIELD MAPS ----------------
FIELD_MAPS = {
    "FCP_Re-Use-Plonge.pdf": {
        "texts": [
            {"key": "FORMATEUR",     "page": 7, "x": 113, "y": 232, "fontSize": 12},
            {"key": "Date",    "page": 7, "x": 82, "y": 268, "fontSize": 12},
            {"key": "NOM", "page": 7, "x": 401, "y": 235, "fontSize": 12},
                ], },
    "FCP-Boissons_Desserts.pdf": {
	 "texts": [
            {"key": "FORMATEUR",     "page": 3, "x": 142, "y": 530, "fontSize": 12},
            {"key": "Date",    "page": 3, "x": 110, "y": 560, "fontSize": 12},
            {"key": "NOM", "page": 3, "x": 410, "y": 530, "fontSize": 12},
                ], },
    "FCP-CLOSE.pdf": {
	 "texts": [
            {"key": "FORMATEUR",     "page": 11, "x": 110, "y": 240, "fontSize": 12},
            {"key": "Date",    "page": 11, "x": 95, "y": 270, "fontSize": 12},
            {"key": "NOM", "page": 11, "x": 400, "y": 240, "fontSize": 12},
                ], },
    "FCP-Cuisson.pdf": {
	 "texts": [
            {"key": "FORMATEUR",     "page": 2, "x": 145, "y": 290, "fontSize": 12},
            {"key": "Date",    "page": 2, "x": 110, "y": 320, "fontSize": 12},
            {"key": "NOM", "page": 2, "x": 410, "y": 290, "fontSize": 12},
                ], },
    "FCP-Cuisson_des_viandes_UHC.pdf": {
	 "texts": [
            {"key": "FORMATEUR",     "page": 2, "x": 130, "y": 255, "fontSize": 12},
            {"key": "Date",    "page": 2, "x": 90, "y": 285, "fontSize": 12},
            {"key": "NOM", "page": 2, "x": 385, "y": 255, "fontSize": 12},
                ], },
    "FCP-Filtrage_de_huile.pdf": {
	 "texts": [
            {"key": "FORMATEUR",     "page": 3, "x": 110, "y": 290, "fontSize": 12},
            {"key": "Date",    "page": 3, "x": 75, "y": 320, "fontSize": 12},
            {"key": "NOM", "page": 3, "x": 400, "y": 290, "fontSize": 12},
                ], },
    "FCP-Frites.pdf": {
	 "texts": [
            {"key": "FORMATEUR",     "page": 2, "x": 125, "y": 260, "fontSize": 12},
            {"key": "Date",    "page": 2, "x": 100, "y": 290, "fontSize": 12},
            {"key": "NOM", "page": 2, "x": 400, "y": 260, "fontSize": 12},
                ], },
    "FCP-Initiation_Assemblage.pdf": {
	 "texts": [
            {"key": "FORMATEUR",     "page": 2, "x": 150, "y": 350, "fontSize": 12},
            {"key": "Date",    "page": 2, "x": 115, "y": 380, "fontSize": 12},
            {"key": "NOM", "page": 2, "x": 410, "y": 350, "fontSize": 12},
                ], },
    "FCP-LOBBY-Acceuil.pdf": {
	 "texts": [
            {"key": "FORMATEUR",     "page": 3, "x": 140, "y": 70, "fontSize": 12},
            {"key": "Date",    "page": 3, "x": 100, "y": 120, "fontSize": 12},
            {"key": "NOM", "page": 3, "x": 410, "y": 70, "fontSize": 12},
                ], },
    "FCP-Livraisons.pdf": {
	 "texts": [
            {"key": "FORMATEUR",     "page": 3, "x": 110, "y": 300, "fontSize": 12},
            {"key": "Date",    "page": 3, "x": 70, "y": 320, "fontSize": 12},
            {"key": "NOM", "page": 3, "x": 400, "y": 300, "fontSize": 12},
                ], },
    "FCP-McCafe.pdf": {
	 "texts": [
            {"key": "FORMATEUR",     "page": 2, "x": 150, "y": 560, "fontSize": 12},
            {"key": "Date",    "page": 2, "x": 120, "y": 590, "fontSize": 12},
            {"key": "NOM", "page": 2, "x": 410, "y": 560, "fontSize": 12},
                ], },
    "FCP-OAT_VERIF_PASS.pdf": {
	 "texts": [
            {"key": "FORMATEUR",     "page": 3, "x": 150, "y": 470, "fontSize": 12},
            {"key": "Date",    "page": 3, "x": 120, "y": 500, "fontSize": 12},
            {"key": "NOM", "page": 3, "x": 410, "y": 470, "fontSize": 12},
                ], },
    "FCP-OPEN.pdf": {
	 "texts": [
            {"key": "FORMATEUR",     "page": 7, "x": 110, "y": 740, "fontSize": 12},
            {"key": "Date",    "page": 7, "x": 85, "y": 770, "fontSize": 12},
            {"key": "NOM", "page": 7, "x": 410, "y": 740, "fontSize": 12},
                ], },
    "FCP-Petit_dejeuner.pdf": {
	 "texts": [
            {"key": "FORMATEUR",     "page": 3, "x": 150, "y": 360, "fontSize": 12},
            {"key": "Date",    "page": 3, "x": 120, "y": 390, "fontSize": 12},
            {"key": "NOM", "page": 3, "x": 410, "y": 360, "fontSize": 12},
                ], },
    "FCP-Prise_de_co_Encaissement.pdf": {
	 "texts": [
            {"key": "FORMATEUR",     "page": 3, "x": 140, "y": 500, "fontSize": 12},
            {"key": "Date",    "page": 3, "x": 120, "y": 530, "fontSize": 12},
            {"key": "NOM", "page": 3, "x": 410, "y": 500, "fontSize": 12},
                ], },
    "FCP-Tempering.pdf": {
	 "texts": [
            {"key": "FORMATEUR",     "page": 2, "x": 140, "y": 160, "fontSize": 12},
            {"key": "Date",    "page": 2, "x": 120, "y": 190, "fontSize": 12},
            {"key": "NOM", "page": 2, "x": 410, "y": 160, "fontSize": 12},
                ], },
}

# ---------------- DB ----------------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- ROUTE D’ACCUEIL ----------------
@app.route("/")
def index():
    return "✅ Serveur Flask en ligne et opérationnel ! Utilise /clients, /employes, /remplissages, /pdfs ..."

# ---------------- CLIENTS ----------------
@app.route("/clients", methods=["GET"])
def get_clients():
    conn = get_conn()
    rows = conn.execute("SELECT nom FROM clients ORDER BY nom").fetchall()
    conn.close()
    return jsonify([r["nom"] for r in rows])

@app.route("/clients", methods=["POST"])
def add_client():
    data = request.json
    if not data or "nom" not in data:
        return "Nom requis", 400
    conn = get_conn()
    try:
        conn.execute("INSERT INTO clients (nom) VALUES (?)", (data["nom"],))
        conn.commit()
        conn.close()
        return "Client ajouté", 201
    except sqlite3.IntegrityError:
        conn.close()
        return "Client existe déjà", 400

@app.route("/clients/<nom>", methods=["DELETE"])
def delete_client(nom):
    conn = get_conn()
    conn.execute("DELETE FROM clients WHERE nom=?", (nom,))
    conn.commit()
    conn.close()
    return "Client supprimé", 200

# ---------------- EMPLOYÉS ----------------
@app.route("/employes", methods=["GET"])
def get_employes():
    conn = get_conn()
    rows = conn.execute("SELECT nom FROM employes ORDER BY nom").fetchall()
    conn.close()
    return jsonify([r["nom"] for r in rows])

@app.route("/employes", methods=["POST"])
def add_employe():
    data = request.json
    if not data or "nom" not in data:
        return "Nom requis", 400
    conn = get_conn()
    try:
        conn.execute("INSERT INTO employes (nom) VALUES (?)", (data["nom"],))
        conn.commit()
        conn.close()
        return "Employé ajouté", 201
    except sqlite3.IntegrityError:
        conn.close()
        return "Employé existe déjà", 400

@app.route("/employes/<nom>", methods=["DELETE"])
def delete_employe(nom):
    conn = get_conn()
    conn.execute("DELETE FROM employes WHERE nom=?", (nom,))
    conn.commit()
    conn.close()
    return "Employé supprimé", 200

# ---------------- REMPLISSAGES ----------------
@app.route("/remplissages", methods=["GET"])
def get_remplissages():
    conn = get_conn()
    rows = conn.execute("SELECT client_nom, pdf_modele, statut, employe_nom, date_remplissage FROM remplissages").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/remplissages", methods=["POST"])
def update_remplissage():
    data = request.json
    if not data or not all(k in data for k in ("client_nom", "pdf_modele", "statut")):
        return "Données incomplètes", 400

    client_nom = data["client_nom"]
    pdf_modele = data["pdf_modele"]
    statut = data["statut"]
    employe_nom = data.get("employe_nom", None)
    date_remplissage = datetime.now().strftime("%Y-%m-%d")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM remplissages WHERE client_nom=? AND pdf_modele=?", (client_nom, pdf_modele))
    row = cur.fetchone()
    if row:
        conn.execute("UPDATE remplissages SET statut=?, employe_nom=?, date_remplissage=? WHERE client_nom=? AND pdf_modele=?",
                     (statut, employe_nom, date_remplissage, client_nom, pdf_modele))
    else:
        conn.execute("INSERT INTO remplissages (client_nom, pdf_modele, statut, employe_nom, date_remplissage) VALUES (?,?,?,?,?)",
                     (client_nom, pdf_modele, statut, employe_nom, date_remplissage))
    conn.commit()
    conn.close()
    return "Remplissage mis à jour", 200

# ---------------- PDF ----------------
@app.route("/pdfs", methods=["GET"])
def list_pdfs():
    files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
    return jsonify(files)

@app.route("/pdfs/<filename>", methods=["GET"])
def get_pdf(filename):
    path = os.path.join(PDF_DIR, filename)
    if not os.path.exists(path):
        return "Fichier introuvable", 404
    return send_file(path, as_attachment=False)

@app.route("/fill-pdf", methods=["POST"])
def fill_pdf():
    data = request.get_json()

    # 1) Vérif des champs
    client = data.get("client")
    employe = data.get("employe", "")
    pdf_modele = data.get("pdf_modele")

    if not client or not pdf_modele:
        return jsonify({"error": "Champs obligatoires manquants (client, pdf_modele)."}), 400

    # 2) Vérif mapping
    if pdf_modele not in FIELD_MAPS:
        return jsonify({"error": f"Aucun mapping FIELD_MAPS pour {pdf_modele}"}), 400

    # 3) Vérif fichier source
    source_path = os.path.join("pdfs", pdf_modele)
    if not os.path.exists(source_path):
        return jsonify({"error": f"Le fichier source {pdf_modele} est introuvable dans /pdfs"}), 404

    # 4) Générer le dossier du client
    client_dir = os.path.join("remplis", client)
    os.makedirs(client_dir, exist_ok=True)

    # 5) Nom du fichier rempli
    date_str = date.today().isoformat()
    output_filename = f"{os.path.splitext(pdf_modele)[0]}_{date_str}.pdf"
    output_path = os.path.join(client_dir, output_filename)

    try:
        # ➝ Ici tu gardes ton code ReportLab / PyPDF2 qui écrit les champs
        # Exemple simple (juste copier le fichier source pour le test) :
        import shutil
        shutil.copy(source_path, output_path)

        return jsonify({
            "message": "PDF généré avec succès",
            "client": client,
            "employe": employe,
            "pdf_modele": pdf_modele,
            "output": output_path
        }), 200

    except Exception as e:
        return jsonify({"error": f"Erreur interne lors du remplissage PDF : {str(e)}"}), 500


# ---------------- MAIN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)





