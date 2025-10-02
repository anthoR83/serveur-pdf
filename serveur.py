 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/serveur.py b/serveur.py
index bfde1cccbb2e891dfe6ae89576fedf98a6d562e1..566ae85563b68b1f9cf732432e6bd580520427ea 100644
--- a/serveur.py
+++ b/serveur.py
@@ -1,43 +1,41 @@
-from flask import Flask, request, jsonify, send_file
-import sqlite3, os
-from datetime import datetime
+from flask import Flask, request, jsonify, send_file, send_from_directory
+import sqlite3, os
+from datetime import datetime, date
 from reportlab.pdfgen import canvas
 from reportlab.lib.pagesizes import letter
 from PyPDF2 import PdfReader, PdfWriter
 from io import BytesIO
 
 app = Flask(__name__)
 
 DB_PATH = "app.db"
 PDF_DIR = "pdfs"
 REMPLIS_DIR = "remplis"
 
-os.makedirs(PDF_DIR, exist_ok=True)
-os.makedirs(REMPLIS_DIR, exist_ok=True)
-
-from flask import send_from_directory
+os.makedirs(PDF_DIR, exist_ok=True)
+os.makedirs(REMPLIS_DIR, exist_ok=True)
 
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
@@ -220,83 +218,77 @@ def update_remplissage():
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
 
-from flask import Flask, request, jsonify, send_file
-import os, datetime
-
-app = Flask(__name__)
-
-
-@app.route("/fill-pdf", methods=["POST"])
-def fill_pdf():
+@app.route("/fill-pdf", methods=["POST"])
+def fill_pdf():
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
-    date_str = datetime.date.today().isoformat()
+    date_str = date.today().isoformat()
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
 
EOF
)
