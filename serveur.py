# serveur.py
import os
import re
import sqlite3
from datetime import datetime
from flask import (
    Flask, request, jsonify, send_from_directory, abort,
    render_template_string, Response
)

BASE_DIR    = os.path.abspath(os.path.dirname(__file__))
DB_PATH     = os.path.join(BASE_DIR, "app.db")
PDF_DIR     = os.path.join(BASE_DIR, "pdfs")
REMPLIS_DIR = os.path.join(BASE_DIR, "remplis")
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(REMPLIS_DIR, exist_ok=True)

app = Flask(__name__)

# --- Base SQLite
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_schema():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS clients (nom TEXT PRIMARY KEY)""")
    c.execute("""CREATE TABLE IF NOT EXISTS employes (nom TEXT PRIMARY KEY)""")
    c.execute("""
        CREATE TABLE IF NOT EXISTS remplissages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_nom   TEXT,
            pdf_modele   TEXT,
            statut       TEXT CHECK(statut IN ('i','s','v')),
            employe_nom  TEXT,
            fichier_path TEXT,
            date_remplissage TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_nom)  REFERENCES clients(nom),
            FOREIGN KEY (employe_nom) REFERENCES employes(nom)
        )
    """)
    conn.commit()
    conn.close()

ensure_schema()

def safe_component(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"[^A-Za-z0-9 ._-]", "_", s)
    s = s.replace("..", "_")
    return s

# --- FIELD MAPS (à ajuster pour tes PDF)
# Coordonnées en points PDF, origine en bas-gauche ; page = 1 pour la 1ère page.
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

# ----------------- HTML INDEX -----------------
INDEX_HTML = """
<!doctype html><html lang="fr"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Remplir & Envoyer PDF</title>
<link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>
<script src="https://unpkg.com/pdf-lib@1.17.1/dist/pdf-lib.min.js"></script>
<style>
body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:16px}
label{display:block;margin:8px 0 4px}
select,input,button{width:100%;padding:10px;font-size:16px}
.grid{display:grid;grid-template-columns:1fr;gap:16px}
@media(min-width:1024px){.grid{grid-template-columns:360px 1fr}}
iframe{width:100%;height:720px;border:1px solid #ccc;border-radius:6px;background:#f8f8f8}
.fieldgroup{border:1px solid #ddd;border-radius:8px;padding:10px;margin-bottom:12px}
.ok{color:green;margin-top:8px}.err{color:#c00;margin-top:8px}
.btn{padding:12px;border:1px solid #ccc;border-radius:6px;background:#f7f7f7}
.small{font-size:13px;color:#666}
</style>
</head><body>
<div class="grid">
  <div>
    <h2>Remplir & Envoyer</h2>
    <label>Client</label><select id="client"></select>
    <label>PDF (modèle)</label><select id="pdf"></select>
    <div class="small">Calage coordonnées : <a id="coordlink" target="_blank">/coord</a></div>
    <label>Statut</label>
    <select id="statut"><option value="i">Initiale (i)</option><option value="s">Suivie (s)</option><option value="v">Validation (v)</option></select>
    <label>Employé</label><select id="employe"></select>

    <div class="fieldgroup">
      <h4>Champs texte</h4>
      <div id="textFields"></div>
    </div>
    <button id="send" class="btn">Générer & Envoyer</button>
    <div id="msg"></div>
  </div>

  <div>
    <h3>Aperçu multi-pages</h3>
    <iframe id="viewer" title="Aperçu PDF"></iframe>
  </div>
</div>

<script>
const els = { client:$('#client'), employe:$('#employe'), pdf:document.getElementById('pdf'),
              statut:document.getElementById('statut'), viewer:document.getElementById('viewer'),
              coord:document.getElementById('coordlink'), textBox:document.getElementById('textFields'),
              send:document.getElementById('send'), msg:document.getElementById('msg') };

let templateBytes=null, currentMap={texts:[]};

async function fetchJSON(u){ const r=await fetch(u); return await r.json(); }

async function loadLists(){
  const [clients, employes, pdfs] = await Promise.all([fetchJSON('/clients'), fetchJSON('/employes'), fetchJSON('/pdfs')]);
  els.client.html(clients.map(c=>`<option>${c}</option>`).join(''));
  els.employe.html(employes.map(e=>`<option>${e}</option>`).join(''));
  document.getElementById('pdf').innerHTML = pdfs.map(p=>`<option>${p}</option>`).join('');
  els.client.select2({ width:'100%', placeholder:"Choisir un client" });
  els.employe.select2({ width:'100%', placeholder:"Choisir un employé" });
  if (pdfs.length) await selectPdf(pdfs[0]);
  document.getElementById('pdf').addEventListener('change', ()=>selectPdf(document.getElementById('pdf').value));
}

async function selectPdf(fileName){
  els.viewer.src = '/view?file='+encodeURIComponent(fileName);
  els.coord.href = '/coord?file='+encodeURIComponent(fileName);
  const r = await fetch('/pdf/raw/'+encodeURIComponent(fileName));
  if(!r.ok){ show('err','Impossible de charger'); return; }
  templateBytes = await r.arrayBuffer();
  currentMap = await fetchJSON('/fieldmap/'+encodeURIComponent(fileName));
  buildForm(currentMap);
}

function buildForm(map){
  els.textBox.innerHTML='';
  (map.texts||[]).forEach(t=>{
    const id='t_'+t.key;
    els.textBox.insertAdjacentHTML('beforeend', `<label for="${id}">${t.key}</label><input id="${id}" type="text" style="width:100%;padding:8px;margin-bottom:8px">`);
  });
}

function readValues(){
  const texts={}; (currentMap.texts||[]).forEach(t=>{
    const el=document.getElementById('t_'+t.key); texts[t.key]=el?el.value:'';
  }); return {texts};
}

function show(kind,msg){ els.msg.className=kind; els.msg.textContent=msg; }

els.send.addEventListener('click', async ()=>{
  if(!templateBytes) return show('err','Pas de modèle');
  const client=els.client.val(), employe=els.employe.val(), pdf=document.getElementById('pdf').value, statut=els.statut.value;
  if(!client||!employe) return show('err','Choisis client et employé');
  const {PDFDocument,StandardFonts,rgb}=PDFLib;
  try{
    const pdfDoc=await PDFDocument.load(templateBytes); const font=await pdfDoc.embedFont(StandardFonts.Helvetica);
    const vals=readValues();
    (currentMap.texts||[]).forEach(t=>{
      const v=(vals.texts[t.key]||'').toString(); if(!v) return;
      const page=pdfDoc.getPage((t.page||1)-1);
      page.drawText(v,{x:t.x||0,y:t.y||0,size:t.fontSize||12,font,color:rgb(0,0,0)});
    });
    const bytes=await pdfDoc.save(); const blob=new Blob([bytes],{type:'application/pdf'});
    const form=new FormData(); form.append('client',client); form.append('pdf',pdf); form.append('statut',statut); form.append('employe',employe); form.append('file',blob,'filled_'+pdf);
    const res=await fetch('/upload',{method:'POST',body:form}); const txt=await res.text(); show(res.ok?'ok':'err',txt);
  }catch(e){ show('err','Erreur: '+(e?.message||e)); }
});

loadLists();
</script>
</body></html>
"""

# ----------------- COORD_HTML -----------------
COORD_HTML = """
<!doctype html><html lang="fr"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Coordonnées PDF</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<style>canvas{border:1px solid #aaa;margin:10px;max-width:100%}</style></head>
<body>
<h2>Cliquer sur le PDF → coordonnées</h2>
<div id="pages"></div>
<pre id="out"></pre>
<script>
const params=new URLSearchParams(location.search); const file=params.get('file')||''; 
const pdfUrl=location.origin+'/pdf/'+encodeURIComponent(file);
const CMAP_URL='https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/cmaps/'; 
const WORKER='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js'; 
pdfjsLib.GlobalWorkerOptions.workerSrc=WORKER;
(async ()=>{
  const loading=pdfjsLib.getDocument({url:pdfUrl,cMapUrl:CMAP_URL,cMapPacked:true}); 
  const pdf=await loading.promise; 
  for(let p=1;p<=pdf.numPages;p++){
    const page=await pdf.getPage(p), scale=1.3; 
    const viewport=page.getViewport({scale}); 
    const canvas=document.createElement('canvas'); 
    canvas.width=viewport.width; canvas.height=viewport.height; 
    const ctx=canvas.getContext('2d'); 
    await page.render({canvasContext:ctx,viewport}).promise; 
    canvas.onclick=e=>{
      const rect=canvas.getBoundingClientRect(); 
      const x=(e.clientX-rect.left)*canvas.width/rect.width; 
      const y=canvas.height-(e.clientY-rect.top)*canvas.height/rect.height; 
      document.getElementById('out').textContent='page='+p+' x='+Math.round(x)+' y='+Math.round(y);
    }; 
    document.getElementById('pages').appendChild(canvas);
  }
})();
</script>
</body></html>
"""

# ----------------- VIEW_HTML ------------------
VIEW_HTML = """
<!doctype html><html lang="fr"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Aperçu PDF</title>
<style>body{font-family:sans-serif;margin:10px} .page{margin:8px 0} canvas{border:1px solid #ccc;max-width:100%;height:auto}</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
</head><body>
<div id="pages"></div>
<script>
const params=new URLSearchParams(location.search); 
const file=params.get('file')||''; 
const pdfUrl=location.origin+'/pdf/'+encodeURIComponent(file);
const CMAP_URL='https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/cmaps/'; 
const WORKER='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js'; 
pdfjsLib.GlobalWorkerOptions.workerSrc=WORKER;
(async ()=>{
  const loading=pdfjsLib.getDocument({url:pdfUrl,cMapUrl:CMAP_URL,cMapPacked:true}); 
  const pdf=await loading.promise; 
  for(let p=1;p<=pdf.numPages;p++){
    const page=await pdf.getPage(p), scale=1.2; 
    const viewport=page.getViewport({scale}); 
    const canvas=document.createElement('canvas'); 
    canvas.width=viewport.width; canvas.height=viewport.height; 
    const ctx=canvas.getContext('2d'); 
    await page.render({canvasContext:ctx,viewport}).promise; 
    document.getElementById('pages').appendChild(canvas);
  }
})();
</script>
</body></html>
"""

# ----------------- ROUTES -----------------
@app.route("/")
def index(): return render_template_string(INDEX_HTML)

@app.route("/clients")
def clients():
    conn=get_conn(); rows=conn.execute("SELECT nom FROM clients ORDER BY nom").fetchall(); conn.close()
    return jsonify([r["nom"] for r in rows])

@app.route("/employes")
def employes():
    conn=get_conn(); rows=conn.execute("SELECT nom FROM employes ORDER BY nom").fetchall(); conn.close()
    return jsonify([r["nom"] for r in rows])

@app.route("/pdfs")
def pdfs():
    files=sorted([f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")])
    return jsonify(files)

@app.route("/pdf/<path:filename>")
def serve_pdf(filename):
    fname=os.path.basename(filename); full=os.path.join(PDF_DIR,fname)
    if not (fname.lower().endswith(".pdf") and os.path.isfile(full)): abort(404)
    return send_from_directory(PDF_DIR,fname,mimetype="application/pdf",as_attachment=False)

@app.route("/pdf/raw/<path:filename>")
def serve_pdf_raw(filename):
    fname=os.path.basename(filename); full=os.path.join(PDF_DIR,fname)
    if not (fname.lower().endswith(".pdf") and os.path.isfile(full)): abort(404)
    with open(full,"rb") as f: data=f.read()
    return Response(data,mimetype="application/pdf")

@app.route("/fieldmap/<path:filename>")
def fieldmap(filename):
    fname=os.path.basename(filename)
    return jsonify(FIELD_MAPS.get(fname,{"texts":[],"checks":[],"checkMark":"✓"}))

@app.route("/upload", methods=["POST"])
def upload():
    client=(request.form.get("client") or "").strip()
    pdf=(request.form.get("pdf") or "").strip()
    statut=(request.form.get("statut") or "").strip()
    employe=(request.form.get("employe") or "").strip()
    f=request.files.get("file")
    if not client or not pdf or statut not in ("i","s","v") or not employe or not f:
        return "Champs manquants",400
    if not f.filename.lower().endswith(".pdf"): return "Fichier non PDF",400
    client_dir=os.path.join(REMPLIS_DIR,safe_component(client)); os.makedirs(client_dir,exist_ok=True)
    ts=datetime.now().strftime("%Y%m%d-%H%M%S"); original=safe_component(f.filename)
    if not original.lower().endswith(".pdf"): original+=".pdf"
    save_name=f"{ts}_{original}"; save_path=os.path.join(client_dir,save_name); f.save(save_path)
    conn=get_conn()
    conn.execute("""INSERT INTO remplissages (client_nom,pdf_modele,statut,employe_nom,fichier_path) VALUES (?,?,?,?,?)""",(client,pdf,statut,employe,save_path))
    conn.commit(); conn.close()
    return f"PDF reçu ✅ pour {client} (statut {statut}, employé {employe})",200

@app.route("/coord")
def coord(): return render_template_string(COORD_HTML)

@app.route("/view")
def view_pdf(): return render_template_string(VIEW_HTML)

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
