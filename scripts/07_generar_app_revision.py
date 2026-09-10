"""Genera la aplicación HTML para la revisión humana de las zonas grises.

Lee ``prod/zonas_grises_revisadas.csv`` (con las decisiones ya tomadas, si
las hay) y el archivo de matrícula para adjuntar la institución de cada
programa, y escribe ``prod/revisar_zonas_grises.html``: una aplicación
autocontenida (sin servidor ni dependencias) donde el humano elige INCLUIR o
EXCLUIR por punto, con persistencia en ``localStorage`` y descarga del CSV
``zonas_grises_revisadas.csv`` con las decisiones, legible para el ensamblado.
"""

import csv
import json
from pathlib import Path

import pandas as pd

from sies_musica.texto import normalizar_nombre

RAIZ = Path(__file__).resolve().parent.parent
RUTA_REVISION = RAIZ / "prod" / "zonas_grises_revisadas.csv"
RUTA_SALIDA = RAIZ / "prod" / "revisar_zonas_grises.html"
RUTA_MATRICULA = (
    RAIZ / "datos SIES" / "Matricula_2007_2026_WEB_10_07_2026.csv"
)
INDICE_INSTITUCION = 13
INDICE_NOMBRE = 19


def leer_instituciones() -> dict[str, list[str]]:
    """Mapa nombre_normalizado -> instituciones (ordenadas) que lo ofrecen."""
    df = pd.read_csv(
        RUTA_MATRICULA,
        sep=";",
        dtype=str,
        encoding="cp1252",
        encoding_errors="replace",
        usecols=[INDICE_INSTITUCION, INDICE_NOMBRE],
    )
    df.columns = ["institucion", "carrera"]
    df = df.dropna(subset=["carrera"])
    df["nombre_normalizado"] = df["carrera"].map(normalizar_nombre)
    agrupado = df.groupby("nombre_normalizado")["institucion"].apply(
        lambda serie: sorted(set(serie.dropna()))
    )
    return {nombre: lista for nombre, lista in agrupado.items()}


def leer_decisiones() -> dict[str, dict[str, str]]:
    """Decisiones ya registradas en el template, por nombre_normalizado."""
    decisiones: dict[str, dict[str, str]] = {}
    if not RUTA_REVISION.exists():
        return decisiones
    with open(RUTA_REVISION, encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            decision = fila.get("decision_final", "").strip().upper()
            if decision:
                decisiones[fila["nombre_normalizado"]] = {
                    "decision_final": decision,
                    "categoria_final": fila.get("categoria_final", "").strip(),
                }
    return decisiones


def a_html(
    filas: list[dict[str, str]],
    instituciones: dict[str, list[str]],
    decisiones: dict[str, dict[str, str]],
) -> str:
    """Arma el documento HTML autocontenido."""
    items = []
    for fila in filas:
        nombre = fila["nombre_normalizado"]
        item = dict(fila)
        item["instituciones"] = instituciones.get(nombre, [])
        decidido = decisiones.get(nombre, {})
        item["decision_final"] = decidido.get("decision_final", "")
        item["categoria_final"] = decidido.get("categoria_final", "")
        items.append(item)
    datos = {"items": items}
    datos_json = json.dumps(datos, ensure_ascii=False).replace("</", "<\\/")
    return PLANTILLA.replace("@@DATOS_JSON@@", datos_json)


def main() -> None:
    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(RUTA_REVISION, encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    instituciones = leer_instituciones()
    decisiones = leer_decisiones()
    html = a_html(filas, instituciones, decisiones)
    RUTA_SALIDA.write_text(html, encoding="utf-8")
    print(f"Aplicación escrita en {RUTA_SALIDA}")
    print(f"Puntos para revisar: {len(filas)}")
    print(
        "Con instituciones: "
        f"{sum(1 for f in filas if instituciones.get(f['nombre_normalizado']))}"
    )
    print(f"Decisiones ya registradas: {sum(1 for d in decisiones.values() if d['decision_final'])}")


PLANTILLA = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Revisión humana — Zonas grises</title>
<style>
  :root{
    --bg:#f6f3ee; --card:#ffffff; --ink:#23272f; --muted:#6f7683;
    --line:#e6e1d8; --accent:#1f7a5c; --accent-soft:#e3f2ec;
    --ok:#15803d; --ok-bg:#e9f9ef; --no:#b3261e; --no-bg:#fdeceb;
    --purple:#7c3aed; --teal:#0f766e; --amber:#b45309; --slate:#5b6472;
    --radius:14px; --shadow:0 1px 3px rgba(31,35,39,.05);
  }
  *{box-sizing:border-box}
  html,body{margin:0;padding:0}
  body{
    font-family:"Segoe UI",system-ui,-apple-system,Roboto,Arial,sans-serif;
    background:var(--bg); color:var(--ink); line-height:1.5;
  }
  header{
    position:sticky; top:0; z-index:5;
    background:rgba(255,255,255,.94); backdrop-filter:blur(6px);
    border-bottom:1px solid var(--line); padding:14px 20px 12px;
  }
  .head-wrap{max-width:1100px;margin:0 auto}
  .titulo{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
  h1{font-size:20px;margin:0;letter-spacing:-.2px}
  .sub{color:var(--muted);font-size:13px}
  .contador{font-size:13px;color:var(--muted)}
  .contador strong{color:var(--ink)}
  .progress-track{margin-top:10px;height:8px;border-radius:99px;background:#e7e2d9;overflow:hidden}
  .progress-fill{height:100%;width:0;border-radius:99px;
    background:linear-gradient(90deg,#34a07a,#1f7a5c);transition:width .25s ease}
  .barra{
    margin-top:12px; display:flex; align-items:center; gap:8px; flex-wrap:wrap;
  }
  .chips{display:flex; gap:6px; flex-wrap:wrap}
  .chip{
    border:1px solid var(--line); background:#fff; color:var(--ink);
    font:inherit; font-size:12.5px; font-weight:600;
    padding:5px 11px; border-radius:99px; cursor:pointer; transition:all .15s;
  }
  .chip:hover{border-color:#c9c2b4}
  .chip.active{background:var(--accent); border-color:var(--accent); color:#fff}
  .chip .n{opacity:.75; font-weight:400}
  .barra-acciones{margin-left:auto; display:flex; gap:8px}
  .btn-accion{
    border:1px solid var(--line); background:#fff; color:var(--ink);
    font:inherit; font-size:12.5px; font-weight:600;
    padding:6px 12px; border-radius:99px; cursor:pointer; transition:all .15s;
  }
  .btn-accion:hover{border-color:#9aa; transform:translateY(-1px)}
  .btn-accion.primario{background:var(--accent); border-color:var(--accent); color:#fff}
  .btn-accion.peligro{color:var(--no)}
  .lista{
    max-width:1100px; margin:0 auto; padding:20px;
    display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:14px;
  }
  .card{
    background:var(--card); border:1px solid var(--line); border-radius:var(--radius);
    box-shadow:var(--shadow); padding:16px 18px;
    display:flex; flex-direction:column; gap:10px; transition:border-color .15s, box-shadow .15s;
  }
  .card:hover{box-shadow:0 3px 10px rgba(31,35,39,.08)}
  .card.estado-incluir{border-color:#bfe3cf}
  .card.estado-excluir{border-color:#f2c6c3}
  .card-top{display:flex; align-items:center; gap:8px}
  .origen{
    font-size:11px; font-weight:700; letter-spacing:.3px; text-transform:uppercase;
    padding:3px 9px; border-radius:99px; white-space:nowrap;
  }
  .origen.llm{background:#f1e9fe; color:var(--purple)}
  .origen.hibrido{background:#e0f3f1; color:var(--teal)}
  .origen.artistica{background:#fdf0dd; color:var(--amber)}
  .origen.ambiguo{background:#eceef1; color:var(--slate)}
  .estado-pill{
    margin-left:auto; font-size:11.5px; font-weight:700;
    padding:3px 9px; border-radius:99px;
  }
  .estado-pill.incluir{background:var(--ok-bg); color:var(--ok)}
  .estado-pill.excluir{background:var(--no-bg); color:var(--no)}
  .nombre{margin:0; font-size:16.5px; font-weight:600; line-height:1.35}
  .etiqueta-inst{font-size:12px; color:var(--muted); font-weight:600}
  .inst-list{display:flex; flex-wrap:wrap; gap:6px; margin-top:2px}
  .inst-chip{
    font-size:12px; color:#4a5160; background:#f1eee8;
    border:1px solid #e7e2d9; padding:3px 9px; border-radius:99px;
  }
  .inst-chip.sin-dato{color:var(--muted); font-style:italic}
  .acciones{display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-top:4px}
  .btn{
    border:1px solid var(--line); background:#fff; color:var(--ink);
    font:inherit; font-size:13px; font-weight:700;
    padding:9px 18px; border-radius:10px; cursor:pointer; transition:all .15s;
    flex:1; min-width:110px; text-align:center;
  }
  .btn:hover{transform:translateY(-1px)}
  .btn-incluir:hover{border-color:var(--ok); color:var(--ok)}
  .btn-excluir:hover{border-color:var(--no); color:var(--no)}
  .btn-incluir.active{background:var(--ok); border-color:var(--ok); color:#fff; box-shadow:0 2px 6px rgba(21,128,61,.3)}
  .btn-excluir.active{background:var(--no); border-color:var(--no); color:#fff; box-shadow:0 2px 6px rgba(179,38,30,.3)}
  .selector-cat{width:100%; margin-top:4px}
  select.cat{
    width:100%; font:inherit; font-size:13px; padding:8px 10px;
    border:1px solid var(--line); border-radius:10px; background:#fff; color:var(--ink);
  }
  .aviso-cat{font-size:12px; color:var(--amber); margin-top:4px}
  .quitar{
    background:none; border:none; color:var(--muted); cursor:pointer;
    font:inherit; font-size:12.5px; text-decoration:underline; padding:4px 6px;
  }
  .quitar:hover{color:var(--no)}
  .vacante{
    max-width:1100px; margin:40px auto; text-align:center; color:var(--muted);
  }
  .nota{
    max-width:1100px; margin:0 auto 30px; padding:0 20px;
    font-size:12.5px; color:var(--muted);
  }
  .nota code{background:#eee9e0; padding:1px 5px; border-radius:5px; font-size:12px}
  @media (max-width:640px){
    .lista{grid-template-columns:1fr; padding:14px}
    .barra-acciones{margin-left:0; width:100%; justify-content:flex-end}
  }
</style>
</head>
<body>

<header>
  <div class="head-wrap">
    <div class="titulo">
      <h1>Revisión humana — Zonas grises</h1>
      <span class="sub">Decide por cada punto si se incluye (con categoría) o se excluye. Tu decisión es final: no vuelve a consultar al modelo.</span>
    </div>
    <div class="progress-track" aria-hidden="true"><div class="progress-fill" id="barraProgreso"></div></div>
    <div class="contador"><strong id="textoProgreso">0 / 0</strong> decididos</div>
    <div class="barra">
      <div class="chips" id="filtros" role="group" aria-label="Filtros"></div>
      <div class="barra-acciones">
        <button class="btn-accion" id="btnImportar" title="Cargar un CSV de revisadas para recuperar decisiones">Cargar CSV</button>
        <input type="file" id="inputImportar" accept=".csv,text/csv" hidden>
        <button class="btn-accion" id="btnReiniciar">Reiniciar</button>
        <button class="btn-accion primario" id="btnExportar">Descargar CSV</button>
      </div>
    </div>
  </div>
</header>

<main>
  <div class="lista" id="lista"></div>
  <div class="vacante" id="vacante" hidden>No hay puntos que mostrar con este filtro.</div>
  <div class="nota">
    El botón <b>Descargar CSV</b> genera <code>zonas_grises_revisadas.csv</code> con las columnas del ensamblado
    (<code>decision_final</code> = INCLUIR/EXCLUIR y <code>categoria_final</code> cuando corresponde). Se guarda en utf-8 sin BOM.
    Usa <b>Cargar CSV</b> para recuperar decisiones desde una copia anterior.
  </div>
</main>

<script type="application/json" id="datos">@@DATOS_JSON@@</script>
<script>
"use strict";
var datos = JSON.parse(document.getElementById("datos").textContent);
var items = datos.items;
var CLAVE = "revision_zonas_grises_v1";
var CATEGORIAS = [
  "Pedagogía en música",
  "Composición y arreglos",
  "Interpretación musical",
  "Teoría, musicología e investigación",
  "Formación musical general",
  "Producción musical y sonido",
  "Musicoterapia",
  "Gestión cultural",
  "Otros"
];
var ORIGEN_CLASE = {
  "DUDOSO del LLM": "llm",
  "Híbrido 'sonido y acústica'": "hibrido",
  "Educación artística pura": "artistica",
  "Ambiguo no clasificable": "ambiguo"
};
var estado = {};
var filtro = "todos";

function cargarEstado() {
  var guardado = null;
  try { guardado = JSON.parse(localStorage.getItem(CLAVE) || "null"); } catch (e) { guardado = null; }
  estado = guardado || {};
  items.forEach(function (it) {
    if (!estado[it.nombre_normalizado]) {
      estado[it.nombre_normalizado] = {
        decision_final: it.decision_final || "",
        categoria_final: it.categoria_final || ""
      };
    }
  });
}

function guardarEstado() {
  try { localStorage.setItem(CLAVE, JSON.stringify(estado)); } catch (e) {}
}

function contadores() {
  var c = { todos: items.length, sin: 0, incluir: 0, excluir: 0 };
  items.forEach(function (it) {
    var d = estado[it.nombre_normalizado].decision_final;
    if (d === DECISION_INCLUIR) c.incluir++;
    else if (d === DECISION_EXCLUIR) c.excluir++;
    else c.sin++;
  });
  return c;
}

function escapar(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function filtrar(it) {
  var d = estado[it.nombre_normalizado].decision_final;
  if (filtro === "todos") return true;
  if (filtro === "sin") return d !== DECISION_INCLUIR && d !== DECISION_EXCLUIR;
  if (filtro === "incluir") return d === DECISION_INCLUIR;
  if (filtro === "excluir") return d === DECISION_EXCLUIR;
  if (filtro === "origen-llm") return it.origen === "DUDOSO del LLM";
  if (filtro === "origen-hibrido") return it.origen === "Híbrido 'sonido y acústica'";
  if (filtro === "origen-artistica") return it.origen === "Educación artística pura";
  if (filtro === "origen-ambiguo") return it.origen === "Ambiguo no clasificable";
  return true;
}

function tarjeta(it) {
  var e = estado[it.nombre_normalizado];
  var div = document.createElement("article");
  div.className = "card";
  if (e.decision_final === DECISION_INCLUIR) div.classList.add("estado-incluir");
  if (e.decision_final === DECISION_EXCLUIR) div.classList.add("estado-excluir");

  var top = document.createElement("div");
  top.className = "card-top";

  var origen = document.createElement("span");
  origen.className = "origen " + (ORIGEN_CLASE[it.origen] || "ambiguo");
  origen.textContent = it.origen;
  top.appendChild(origen);

  var pill = document.createElement("span");
  pill.className = "estado-pill";
  if (e.decision_final === DECISION_INCLUIR) {
    pill.classList.add("incluir");
    pill.textContent = "INCLUIR";
  } else if (e.decision_final === DECISION_EXCLUIR) {
    pill.classList.add("excluir");
    pill.textContent = "EXCLUIR";
  } else {
    pill.style.display = "none";
  }
  top.appendChild(pill);
  div.appendChild(top);

  var nombre = document.createElement("h3");
  nombre.className = "nombre";
  nombre.textContent = it.nombre_normalizado;
  div.appendChild(nombre);

  var et = document.createElement("div");
  et.className = "etiqueta-inst";
  et.textContent = "Institución(es)";
  div.appendChild(et);

  var inst = document.createElement("div");
  inst.className = "inst-list";
  if (it.instituciones && it.instituciones.length) {
    it.instituciones.forEach(function (i) {
      var chip = document.createElement("span");
      chip.className = "inst-chip";
      chip.textContent = i;
      inst.appendChild(chip);
    });
  } else {
    var chip2 = document.createElement("span");
    chip2.className = "inst-chip sin-dato";
    chip2.textContent = "sin institución registrada";
    inst.appendChild(chip2);
  }
  div.appendChild(inst);

  var acciones = document.createElement("div");
  acciones.className = "acciones";

  var btnIn = document.createElement("button");
  btnIn.type = "button";
  btnIn.className = "btn btn-incluir";
  btnIn.textContent = "INCLUIR";
  if (e.decision_final === DECISION_INCLUIR) btnIn.classList.add("active");
  btnIn.addEventListener("click", function () {
    if (estado[it.nombre_normalizado].decision_final === DECISION_INCLUIR) {
      estado[it.nombre_normalizado].decision_final = "";
      estado[it.nombre_normalizado].categoria_final = "";
    } else {
      estado[it.nombre_normalizado].decision_final = DECISION_INCLUIR;
    }
    guardarEstado(); render();
  });
  acciones.appendChild(btnIn);

  var btnEx = document.createElement("button");
  btnEx.type = "button";
  btnEx.className = "btn btn-excluir";
  btnEx.textContent = "EXCLUIR";
  if (e.decision_final === DECISION_EXCLUIR) btnEx.classList.add("active");
  btnEx.addEventListener("click", function () {
    if (estado[it.nombre_normalizado].decision_final === DECISION_EXCLUIR) {
      estado[it.nombre_normalizado].decision_final = "";
      estado[it.nombre_normalizado].categoria_final = "";
    } else {
      estado[it.nombre_normalizado].decision_final = DECISION_EXCLUIR;
      estado[it.nombre_normalizado].categoria_final = "";
    }
    guardarEstado(); render();
  });
  acciones.appendChild(btnEx);
  div.appendChild(acciones);

  if (e.decision_final === DECISION_INCLUIR) {
    var select = document.createElement("select");
    select.className = "cat";
    select.setAttribute("aria-label", "Categoría para " + it.nombre_normalizado);
    var opcionVacia = document.createElement("option");
    opcionVacia.value = "";
    opcionVacia.textContent = "— Elegir categoría —";
    select.appendChild(opcionVacia);
    CATEGORIAS.forEach(function (cat) {
      var op = document.createElement("option");
      op.value = cat;
      op.textContent = cat;
      if (cat === e.categoria_final) op.selected = true;
      select.appendChild(op);
    });
    select.addEventListener("change", function () {
      estado[it.nombre_normalizado].categoria_final = select.value;
      guardarEstado(); render();
    });
    div.appendChild(select);

    if (!e.categoria_final) {
      var aviso = document.createElement("div");
      aviso.className = "aviso-cat";
      aviso.textContent = "Elige una categoría para registrar el INCLUIR.";
      div.appendChild(aviso);
    }
  }

  var quitar = document.createElement("button");
  quitar.type = "button";
  quitar.className = "quitar";
  quitar.textContent = "quitar decisión";
  quitar.addEventListener("click", function () {
    estado[it.nombre_normalizado].decision_final = "";
    estado[it.nombre_normalizado].categoria_final = "";
    guardarEstado(); render();
  });
  acciones.appendChild(quitar);

  return div;
}

function render() {
  var lista = document.getElementById("lista");
  lista.textContent = "";
  var visibles = 0;
  items.forEach(function (it) {
    if (filtrar(it)) { lista.appendChild(tarjeta(it)); visibles++; }
  });
  document.getElementById("vacante").hidden = visibles > 0;

  var c = contadores();
  document.getElementById("textoProgreso").textContent =
    (c.incluir + c.excluir) + " / " + items.length;
  document.getElementById("barraProgreso").style.width =
    items.length ? (((c.incluir + c.excluir) / items.length) * 100) + "%" : "0%";

  var chips = document.getElementById("filtros");
  chips.textContent = "";
  var defs = [
    ["todos", "Todos", c.todos],
    ["sin", "Sin decidir", c.sin],
    ["incluir", "Incluidos", c.incluir],
    ["excluir", "Excluidos", c.excluir],
    ["origen-llm", "DUDOSO del LLM", 0],
    ["origen-hibrido", "Sonido y acústica", 0],
    ["origen-artistica", "Ed. artística", 0]
  ];
  defs.forEach(function (d) {
    var chip = document.createElement("button");
    chip.type = "button";
    chip.className = "chip" + (filtro === d[0] ? " active" : "");
    if (d[0] === "origen-llm" || d[0] === "origen-hibrido" || d[0] === "origen-artistica") {
      d[2] = items.filter(function (it) {
        return (d[0] === "origen-llm" && it.origen === "DUDOSO del LLM") ||
               (d[0] === "origen-hibrido" && it.origen === "Híbrido 'sonido y acústica'") ||
               (d[0] === "origen-artistica" && it.origen === "Educación artística pura");
      }).length;
    }
    var label = document.createElement("span");
    label.textContent = d[1] + " ";
    var n = document.createElement("span");
    n.className = "n";
    n.textContent = d[2];
    chip.appendChild(label);
    chip.appendChild(n);
    chip.addEventListener("click", function () {
      filtro = d[0];
      render();
    });
    chips.appendChild(chip);
  });
}

function celdaCSV(v) {
  var s = String(v === null || v === undefined ? "" : v);
  return /[",\\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}

function columnasCSV() {
  return [
    "nombre_normalizado", "nombre_original", "veredicto", "categoria",
    "metodo", "razon", "origen", "decision_final", "categoria_final"
  ];
}

function exportarCSV() {
  var cols = columnasCSV();
  var lineas = [cols.join(",")];
  items.forEach(function (it) {
    var e = estado[it.nombre_normalizado];
    var fila = cols.map(function (c) {
      if (c === "decision_final") return e.decision_final;
      if (c === "categoria_final") return e.categoria_final;
      return it[c] === undefined ? "" : it[c];
    });
    lineas.push(fila.map(celdaCSV).join(","));
  });
  var blob = new Blob([lineas.join("\\r\\n")], { type: "text/csv;charset=utf-8" });
  var a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "zonas_grises_revisadas.csv";
  document.body.appendChild(a);
  a.click();
  setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 0);
  aviso("CSV descargado con " + items.length + " puntos.");
}

function parsearCSV(texto) {
  var filas = [], fila = [], campo = "", enComillas = false;
  for (var i = 0; i < texto.length; i++) {
    var c = texto[i];
    if (enComillas) {
      if (c === '"') {
        if (texto[i + 1] === '"') { campo += '"'; i++; } else { enComillas = false; }
      } else { campo += c; }
    } else if (c === '"') {
      enComillas = true;
    } else if (c === ",") {
      fila.push(campo); campo = "";
    } else if (c === "\\n") {
      fila.push(campo); filas.push(fila); fila = []; campo = "";
    } else if (c !== "\\r") {
      campo += c;
    }
  }
  fila.push(campo);
  if (fila.some(function (x) { return x !== ""; })) filas.push(fila);
  return filas;
}

function importarCSV(texto) {
  var filas = parsearCSV(texto);
  if (!filas.length) { aviso("El archivo no tiene filas."); return; }
  var cabecera = filas[0];
  var idxNombre = cabecera.indexOf("nombre_normalizado");
  var idxDecision = cabecera.indexOf("decision_final");
  var idxCat = cabecera.indexOf("categoria_final");
  if (idxNombre < 0 || idxDecision < 0) { aviso("Formato no reconocido: faltan columnas de decisión."); return; }
  var actualizados = 0;
  filas.slice(1).forEach(function (f) {
    if (idxNombre >= f.length) return;
    var nombre = f[idxNombre];
    if (!estado[nombre]) return;
    var d = (f[idxDecision] || "").trim().toUpperCase();
    if (d === DECISION_INCLUIR || d === DECISION_EXCLUIR) {
      estado[nombre].decision_final = d;
      estado[nombre].categoria_final = idxCat >= 0 && idxCat < f.length ? f[idxCat].trim() : "";
      actualizados++;
    }
  });
  guardarEstado(); render();
  aviso("Se importaron " + actualizados + " decisiones.");
}

var toastTimer = null;
function aviso(mensaje) {
  var t = document.getElementById("toast");
  t.textContent = mensaje;
  t.classList.add("visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(function () { t.classList.remove("visible"); }, 2600);
}

document.getElementById("btnExportar").addEventListener("click", exportarCSV);
document.getElementById("btnReiniciar").addEventListener("click", function () {
  if (!confirm("¿Reiniciar todas las decisiones? Esta acción no se puede deshacer.")) return;
  localStorage.removeItem(CLAVE);
  cargarEstado(); render();
  aviso("Decisiones reiniciadas.");
});
document.getElementById("btnImportar").addEventListener("click", function () {
  document.getElementById("inputImportar").click();
});
document.getElementById("inputImportar").addEventListener("change", function (ev) {
  var archivo = ev.target.files && ev.target.files[0];
  if (!archivo) return;
  var lector = new FileReader();
  lector.onload = function () { importarCSV(String(lector.result)); };
  lector.readAsText(archivo, "utf-8");
  ev.target.value = "";
});

var DECISION_INCLUIR = "INCLUIR";
var DECISION_EXCLUIR = "EXCLUIR";

cargarEstado();
render();
</script>

<div class="toast" id="toast"></div>
<style>
  .toast{
    position:fixed; left:50%; bottom:26px; transform:translateX(-50%) translateY(12px);
    background:#23272f; color:#fff; font-size:13px; padding:10px 18px; border-radius:10px;
    opacity:0; pointer-events:none; transition:opacity .2s, transform .2s; z-index:20;
    box-shadow:0 6px 20px rgba(0,0,0,.25);
  }
  .toast.visible{opacity:1; transform:translateX(-50%) translateY(0)}
</style>
</body>
</html>
"""


if __name__ == "__main__":
    main()
