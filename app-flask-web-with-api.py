#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =============================================================================
# app.py — Flask-интерфейс для редактирования SQLite БД + REST API для воркера
# =============================================================================
#
# БЫСТРЫЙ СТАРТ:
#   1. Положите файл рядом с main-table-project.db
#   2. pip install flask
#   3. python app.py
#   4. Откройте http://your-server:5000 – веб-интерфейс для ручного редактирования
#
# REST API (используется воркером):
#   GET  /api/next_step   – получить следующую задачу (проект + шаг) для анализа
#   POST /api/update_step – сообщить результат выполнения шага
#   GET  /api/status_overview – сводка по всем проектам (опционально)
#
# КАК РАСШИРЯТЬ ПРИЛОЖЕНИЕ (добавление нового шага анализа):
#  1. Добавить колонку в таблицу `status` (например, `status_new_tool`)
#  2. Обновить STEPS_IN_ORDER (порядок выполнения)
#  3. Обновить STEP_DEPENDENCIES (если шаг зависит от других)
#  4. Обновить RESULT_PATH_MAP (если результат шага сохраняется в `results_path`)
#  5. При желании добавить поле в TABLE_CONFIG для отображения в веб-интерфейсе
# =============================================================================

import os
import logging
import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, jsonify

# -----------------------------------------------------------------------------
# ЛОГИРОВАНИЕ
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# -----------------------------------------------------------------------------
# НАСТРОЙКИ БАЗЫ ДАННЫХ
# -----------------------------------------------------------------------------
DB_PATH = 'main-table-project.db'

# -----------------------------------------------------------------------------
# КОНФИГ ТАБЛИЦ ДЛЯ ВЕБ-ИНТЕРФЕЙСА
# -----------------------------------------------------------------------------
TABLE_CONFIG = {
    'status': {
        'dropdown_fields': {
            'status_unpacking':             ['NOT_STARTED', 'PROCESSING', 'SUCCEEDED', 'FAILED', 'false'],
            'status_keep_unpacked':         ['false', 'NOT_STARTED', 'PROCESSING', 'SUCCEEDED', 'FAILED'],
            'status_json_src':              ['NOT_STARTED', 'PROCESSING', 'SUCCEEDED', 'FAILED', 'false'],
            'status_json_bin':              ['NOT_STARTED', 'PROCESSING', 'SUCCEEDED', 'FAILED', 'false'],
            'status_extensions':            ['NOT_STARTED', 'PROCESSING', 'SUCCEEDED', 'FAILED', 'false'],
            'status_binaries_in_src':       ['NOT_STARTED', 'PROCESSING', 'SUCCEEDED', 'FAILED', 'false'],
            'status_SQ':                    ['NOT_STARTED', 'PROCESSING', 'SUCCEEDED', 'FAILED', 'false'],
            'status_svace_ob_build':        ['NOT_STARTED', 'PROCESSING', 'SUCCEEDED', 'FAILED', 'false'],
            'status_svace_ob_analyze':      ['NOT_STARTED', 'PROCESSING', 'SUCCEEDED', 'FAILED', 'false'],
            'status_svacer_ob_analyze':     ['NOT_STARTED', 'PROCESSING', 'SUCCEEDED', 'FAILED', 'false'],
            'status_svace_b_build':         ['NOT_STARTED', 'PROCESSING', 'SUCCEEDED', 'FAILED', 'false'],
            'status_svace_b_build_analyze': ['NOT_STARTED', 'PROCESSING', 'SUCCEEDED', 'FAILED', 'false'],
            'status_buildography_analyze':  ['NOT_STARTED', 'PROCESSING', 'SUCCEEDED', 'FAILED', 'false'],
            'status_izb':                   ['NOT_STARTED', 'PROCESSING', 'SUCCEEDED', 'FAILED', 'false'],
            'status_NOP_PREBUILD':          ['NOT_STARTED', 'PROCESSING', 'SUCCEEDED', 'FAILED', 'false'],
            'status_NOP_POSTBUILD':         ['NOT_STARTED', 'PROCESSING', 'SUCCEEDED', 'FAILED', 'false'],
            'status_understand':            ['NOT_STARTED', 'PROCESSING', 'SUCCEEDED', 'FAILED', 'false'],
            'status_AKVS':                  ['NOT_STARTED', 'PROCESSING', 'SUCCEEDED', 'FAILED', 'false'],
            'status_hash':                  ['NOT_STARTED', 'PROCESSING', 'SUCCEEDED', 'FAILED', 'false'],
            'status_work test':             ['inactive', 'active', 'stollen']
        },
    },
}

# -----------------------------------------------------------------------------
# МАППИНГ: поле статуса → поле пути в таблице results_path
# -----------------------------------------------------------------------------
RESULT_PATH_MAP = {
    'status_extensions':            'extensions_path',
    'status_keep_unpacked':         'keep_unpacked_path',
    'status_json_src':              'json_src_bin_path',
    'status_json_bin':              'json_src_bin_path',
    'status_binaries_in_src':       'binsrc_path',
    'status_SQ':                    'SQ_result_path',
    'status_svace_ob_build':        'svace_ob_build_path',
    'status_svace_ob_analyze':      'svace_ob_analyze_path',
    'status_svacer_ob_analyze':     'svace_svacer_ob_analyze_path',
    'status_svace_b_build':         'svace_b_build_path',
    'status_svace_b_build_analyze': 'svace_b_analyze_path',
    'status_buildography_analyze':  'buildography_analyze_path',
    'status_NOP_PREBUILD':          'path_nop_prebuild',
    'status_NOP_POSTBUILD':         'path_nop_postbuild',
    'status_understand':            'understand_path',
    'status_izb':                   'izb_path',
    'status_AKVS':                  'AKVS_path',
    'status_hash':                  'hash_path',
}

# -----------------------------------------------------------------------------
# НАСТРОЙКИ ПОРЯДКА ВЫПОЛНЕНИЯ ШАГОВ И ЗАВИСИМОСТЕЙ ДЛЯ API
# -----------------------------------------------------------------------------
STEPS_IN_ORDER = [
    "status_unpacking",
    "status_hash",
    "status_extensions",
    "status_binaries_in_src",
    "status_json_src",
    "status_json_bin",
    "status_svace_ob_build",
    "status_svace_ob_analyze",
    "status_svacer_ob_analyze",
    "status_buildography_analyze",
    "status_izb",
    "status_SQ",
]

STEP_DEPENDENCIES = {
    "status_hash":                  ["status_unpacking"],
    "status_extensions":            ["status_unpacking"],
    "status_binaries_in_src":       ["status_extensions"],
    "status_json_src":              ["status_unpacking"],
    "status_json_bin":              ["status_unpacking"],
    "status_svace_ob_build":        ["status_unpacking", "status_extensions"],
    "status_svace_ob_analyze":      ["status_svace_ob_build"],
    "status_svacer_ob_analyze":     ["status_svace_ob_analyze"],
    "status_buildography_analyze":  ["status_json_src", "status_json_bin"],
    "status_izb":                   ["status_buildography_analyze", "status_binaries_in_src"],
    "status_SQ":                    ["status_unpacking", "status_extensions",
                                     "status_json_src", "status_json_bin"],
}

# Белые списки для защиты от SQL-инъекций (используются в API)
ALLOWED_STEPS = set(STEPS_IN_ORDER)
ALLOWED_PATH_FIELDS = set(RESULT_PATH_MAP.values())

# =============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ (общие для веба и API)
# =============================================================================

def get_db():
    """Возвращает подключение к SQLite с row_factory = sqlite3.Row."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Включаем WAL-режим для лучшей конкурентности при нескольких воркерах
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

HIDDEN_TABLES = {'sqlite_sequence'}

def get_all_tables(conn):
    """Возвращает список пользовательских таблиц БД (исключая служебные)."""
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    return [r['name'] for r in rows if r['name'] not in HIDDEN_TABLES]

class ColInfo:
    """Информация о колонке таблицы: имя и тип."""
    def __init__(self, name, col_type):
        self.name = name
        self.type_upper = (col_type or 'TEXT').upper().split('(')[0].strip()

def get_columns(conn, table):
    """Возвращает список ColInfo для указанной таблицы."""
    rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    return [ColInfo(r['name'], r['type']) for r in rows]

# =============================================================================
# ВЕБ-ИНТЕРФЕЙС
# =============================================================================

HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>{{ table }} — Project Status</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Syne:wght@700;800&display=swap');
  :root {
    --bg: #0e0e11;
    --surface: #16161a;
    --border: #2a2a32;
    --accent: #7fff6e;
    --accent3: #6eb5ff;
    --text: #e8e8f0;
    --muted: #6b6b80;
    --success: #7fff6e;
    --failure: #ff6b6b;
    --na: #6b6b80;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'JetBrains Mono', monospace;
    min-height: 100vh;
    padding: 2rem;
  }
  header {
    margin-bottom: 1.5rem;
    border-left: 3px solid var(--accent);
    padding-left: 1rem;
  }
  header h1 {
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.03em;
  }
  header p { color: var(--muted); font-size: 0.75rem; margin-top: 0.2rem; }
  .table-nav {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
  }
  .tab {
    padding: 0.3rem 0.8rem;
    border-radius: 4px;
    font-size: 0.72rem;
    font-family: 'JetBrains Mono', monospace;
    cursor: pointer;
    text-decoration: none;
    border: 1px solid var(--border);
    color: var(--muted);
    transition: all 0.15s;
  }
  .tab:hover { color: var(--text); border-color: var(--muted); }
  .tab.active { background: var(--accent); color: #000; border-color: var(--accent); font-weight: 600; }
  .flash {
    background: #1a2a1a; border: 1px solid var(--accent);
    color: var(--accent); padding: 0.6rem 1rem;
    font-size: 0.75rem; margin-bottom: 1.5rem; border-radius: 4px;
  }
  .toolbar {
    display: flex; gap: 0.75rem; margin-bottom: 1.25rem;
    align-items: center; flex-wrap: wrap;
  }
  .search-box {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 4px; color: var(--text);
    font-family: 'JetBrains Mono', monospace; font-size: 0.75rem;
    padding: 0.4rem 0.75rem; width: 240px; transition: border-color 0.15s;
  }
  .search-box:focus { outline: none; border-color: var(--accent); }
  .search-box::placeholder { color: var(--muted); }
  .btn {
    border-radius: 4px; padding: 0.4rem 0.9rem;
    font-family: 'JetBrains Mono', monospace; font-size: 0.72rem;
    font-weight: 600; cursor: pointer; border: none;
    transition: opacity 0.15s; white-space: nowrap;
    text-decoration: none; display: inline-block;
  }
  .btn:hover { opacity: 0.85; }
  .btn-green { background: var(--accent); color: #000; }
  .btn-ghost {
    background: transparent; color: var(--muted);
    border: 1px solid var(--border);
  }
  .btn-ghost:hover { color: var(--text); border-color: var(--muted); }
  .count { color: var(--muted); font-size: 0.72rem; margin-left: auto; }
  .add-panel {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; padding: 1.25rem;
    margin-bottom: 1.5rem; display: none;
  }
  .add-panel.open { display: block; }
  .add-panel h2 {
    font-family: 'Syne', sans-serif; font-size: 1rem;
    margin-bottom: 1rem; color: var(--accent);
  }
  .add-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 0.75rem; margin-bottom: 1rem;
  }
  .field-group label {
    display: block; font-size: 0.62rem; color: var(--muted);
    text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem;
  }
  .field-group input, .field-group select {
    width: 100%; background: var(--bg); border: 1px solid var(--border);
    border-radius: 4px; color: var(--text);
    font-family: 'JetBrains Mono', monospace; font-size: 0.72rem;
    padding: 0.35rem 0.5rem;
  }
  .field-group input:focus, .field-group select:focus {
    outline: none; border-color: var(--accent);
  }
  .add-actions { display: flex; gap: 0.5rem; }
  .table-wrap {
    overflow-x: auto; border: 1px solid var(--border); border-radius: 8px;
  }
  table { width: 100%; border-collapse: collapse; font-size: 0.72rem; }
  thead tr { background: #111116; border-bottom: 1px solid var(--border); }
  th {
    padding: 0.7rem 0.5rem; text-align: left; color: var(--muted);
    font-weight: 600; font-size: 0.63rem;
    text-transform: uppercase; letter-spacing: 0.05em;
    vertical-align: bottom;
  }
  th a {
    display: inline-block;
    white-space: nowrap;
  }
  th.sortable { cursor: pointer; user-select: none; }
  th.sortable:hover { color: var(--text); }
  th.sort-asc a::after  { content: ' ↑'; color: var(--accent); }
  th.sort-desc a::after { content: ' ↓'; color: var(--accent); }
  td { padding: 0.6rem 0.8rem; border-bottom: 1px solid var(--border); vertical-align: middle; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: #1a1a20; }
  .cell-text { max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .cell-name { font-weight: 600; color: var(--accent3); }
  .cell-muted { color: var(--muted); }
  input.inline-edit {
    background: transparent; border: none; border-bottom: 1px solid transparent;
    color: var(--text); font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem; width: 100%; min-width: 80px; padding: 0.1rem 0;
    transition: border-color 0.15s;
  }
  input.inline-edit:focus { outline: none; border-bottom-color: var(--accent); background: #1a1a20; }
  input.inline-edit[type=number] { width: 70px; }
  select.inline {
    background: var(--surface); color: var(--text);
    border: 1px solid var(--border); border-radius: 4px;
    padding: 0.25rem 0.4rem; font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; cursor: pointer; width: 115px;
  }
  select.inline:focus { outline: none; border-color: var(--accent); }
  select.inline.success { color: var(--success); border-color: #2a4a2a; }
  select.inline.failure { color: var(--failure); border-color: #4a2a2a; }
  select.inline.na      { color: var(--na); }
  .btn-save {
    background: var(--accent); color: #000; border: none;
    border-radius: 4px; padding: 0.3rem 0.7rem;
    font-family: 'JetBrains Mono', monospace; font-size: 0.7rem;
    font-weight: 600; cursor: pointer; white-space: nowrap; transition: opacity 0.15s;
  }
  .btn-save:hover { opacity: 0.85; }
  .btn-del {
    background: transparent; color: var(--muted);
    border: 1px solid var(--border); border-radius: 4px;
    padding: 0.3rem 0.6rem; font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; cursor: pointer; transition: all 0.15s; margin-left: 0.4rem;
  }
  .btn-del:hover { color: var(--failure); border-color: var(--failure); }
  .actions { white-space: nowrap; }
  .empty { text-align: center; padding: 3rem; color: var(--muted); }
  .path-btn {
    background: transparent; border: none; cursor: pointer;
    color: var(--muted); font-size: 0.8rem; padding: 0 0.2rem;
    vertical-align: middle; transition: color 0.15s;
    position: relative;
  }
  .path-btn:hover { color: var(--accent3); }
  .path-popup {
    display: none;
    position: fixed;
    background: #1e1e26;
    border: 1px solid var(--accent3);
    border-radius: 6px;
    padding: 0.6rem 0.8rem;
    font-size: 0.7rem;
    color: var(--text);
    z-index: 1000;
    max-width: 400px;
    word-break: break-all;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  }
  .path-popup .popup-label {
    color: var(--muted); font-size: 0.6rem;
    text-transform: uppercase; letter-spacing: 0.05em;
    margin-bottom: 0.3rem;
  }
  .path-popup .popup-path {
    color: var(--accent3); margin-bottom: 0.4rem;
  }
  .path-popup .popup-copy {
    background: var(--accent3); color: #000; border: none;
    border-radius: 3px; padding: 0.2rem 0.5rem;
    font-family: 'JetBrains Mono', monospace; font-size: 0.65rem;
    font-weight: 600; cursor: pointer;
  }
  .path-popup .popup-copy:hover { opacity: 0.85; }
</style>
</head>
<body>
<header>
  <h1>Project Status</h1>
  <p>{{ total }} row(s) in <strong>{{ table }}</strong></p>
</header>
<div class="table-nav">
  {% for t in all_tables %}
  <a class="tab {% if t == table %}active{% endif %}" href="/?table={{ t }}">{{ t }}</a>
  {% endfor %}
</div>
{% if msg %}<div class="flash">{{ msg }}</div>{% endif %}
<div class="toolbar">
  <form method="GET" action="/" style="display:contents">
    <input type="hidden" name="table" value="{{ table }}">
    <input class="search-box" type="text" name="q" value="{{ q }}" placeholder="search…">
    <button class="btn btn-ghost" type="submit">search</button>
    {% if q %}<a href="/?table={{ table }}" class="btn btn-ghost">clear</a>{% endif %}
  </form>
  <button class="btn btn-green" onclick="toggleAdd()">+ add row</button>
  <span class="count">showing {{ rows|length }}{% if q %} of {{ total }}{% endif %}</span>
</div>
<div class="add-panel" id="addPanel">
  <h2>New row in {{ table }}</h2>
  <form method="POST" action="/add">
    <input type="hidden" name="table" value="{{ table }}">
    <div class="add-grid">
      {% for col in columns %}
        {% if col.name != 'id' %}
        <div class="field-group">
          <label>{{ col.name }}</label>
          {% if col.name in dropdown_fields %}
            <select name="{{ col.name }}">
              {% for opt in dropdown_fields[col.name] %}
              <option value="{{ opt }}">{{ opt or '—' }}</option>
              {% endfor %}
            </select>
          {% elif col.type_upper in ('INTEGER', 'REAL', 'NUMERIC') %}
            <input type="number" name="{{ col.name }}" placeholder="0">
          {% else %}
            <input type="text" name="{{ col.name }}" placeholder="{{ col.name }}">
          {% endif %}
        </div>
        {% endif %}
      {% endfor %}
    </div>
    <div class="add-actions">
      <button type="submit" class="btn btn-green">save</button>
      <button type="button" class="btn btn-ghost" onclick="toggleAdd()">cancel</button>
    </div>
  </form>
</div>
<div class="table-wrap">
  <table>
    <thead>
      <tr>
        {% for col in columns %}
        <th class="sortable {% if sort == col.name %}sort-{{ order }}{% endif %}">
          <a href="/?table={{ table }}&sort={{ col.name }}&order={{ 'asc' if (sort==col.name and order=='desc') else 'desc' if (sort==col.name and order=='asc') else 'asc' }}&q={{ q }}"
             style="color:inherit;text-decoration:none">{{ col.name }}</a>
        </th>
        {% endfor %}
        <th>actions</th>
      </tr>
    </thead>
    <tbody>
    {% if rows %}
      {% for row in rows %}
      <form method="POST" action="/update">
        <input type="hidden" name="id" value="{{ row['id'] }}">
        <input type="hidden" name="table" value="{{ table }}">
        <input type="hidden" name="q" value="{{ q }}">
        <input type="hidden" name="sort" value="{{ sort }}">
        <input type="hidden" name="order" value="{{ order }}">
        <tr>
          {% for col in columns %}
          <td>
            {% if col.name == 'id' %}
              <span style="color:var(--muted)">{{ row[col.name] }}</span>
            {% elif col.name in dropdown_fields %}
              <div style="display:inline-flex;align-items:center;gap:0.3rem;white-space:nowrap;">
                <select name="{{ col.name }}" class="inline {{ row[col.name] or '' }}"
                        onchange="this.className='inline '+this.value">
                  {% for opt in dropdown_fields[col.name] %}
                  <option value="{{ opt }}" {% if row[col.name]==opt %}selected{% endif %}>{{ opt or '—' }}</option>
                  {% endfor %}
                </select>
                {% if col.name in result_path_map and row['project_name'] in result_paths %}
                  {% set path_field = result_path_map[col.name] %}
                  {% set path_val = result_paths[row['project_name']].get(path_field, '') %}
                  {% if path_val %}
                  <button type="button" class="path-btn"
                    onclick="showPathPopup(event, '{{ path_val|e }}')"
                    title="Путь к результатам">📁</button>
                  {% endif %}
                {% endif %}
              </div>
            {% elif col.type_upper in ('INTEGER', 'REAL', 'NUMERIC') %}
              <input class="inline-edit" type="number" name="{{ col.name }}" value="{{ row[col.name] or '' }}">
            {% else %}
              <input class="inline-edit" type="text" name="{{ col.name }}" value="{{ row[col.name] or '' }}">
            {% endif %}
          </td>
          {% endfor %}
          <td class="actions">
            <button type="submit" class="btn-save">save</button>
            <button type="button" class="btn-del"
              onclick="if(confirm('Delete this row?')) window.location='/delete/{{ row['id'] }}?table={{ table }}&q={{ q }}&sort={{ sort }}&order={{ order }}'">del</button>
          </td>
        </tr>
      </form>
      {% endfor %}
    {% else %}
      <tr><td colspan="100" class="empty">
        {% if q %}no results for "{{ q }}"{% else %}no rows{% endif %}
      </td></tr>
    {% endif %}
    </tbody>
  </table>
</div>
<div class="path-popup" id="pathPopup">
  <div class="popup-label">Путь к результатам</div>
  <div class="popup-path" id="pathPopupText"></div>
  <button class="popup-copy" onclick="copyPath()">копировать</button>
</div>
<script>
function toggleAdd() {
  document.getElementById('addPanel').classList.toggle('open');
}
function showPathPopup(event, path) {
  event.stopPropagation();
  const popup = document.getElementById('pathPopup');
  document.getElementById('pathPopupText').textContent = path;
  popup.style.display = 'block';
  const rect = event.target.getBoundingClientRect();
  let left = rect.right + 8;
  let top = rect.top + window.scrollY;
  if (left + 420 > window.innerWidth) left = rect.left - 428;
  popup.style.left = left + 'px';
  popup.style.top = top + 'px';
}
function copyPath() {
  const text = document.getElementById('pathPopupText').textContent;
  const btn = document.querySelector('.popup-copy');
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(() => {
      btn.textContent = 'скопировано!';
      setTimeout(() => btn.textContent = 'копировать', 1500);
    });
  } else {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    btn.textContent = 'скопировано!';
    setTimeout(() => btn.textContent = 'копировать', 1500);
  }
}
document.addEventListener('click', function(e) {
  const popup = document.getElementById('pathPopup');
  if (!popup.contains(e.target) && !e.target.classList.contains('path-btn')) {
    popup.style.display = 'none';
  }
});
</script>
</body>
</html>
"""

@app.route('/')
def index():
    msg = request.args.get('msg')
    q = request.args.get('q', '').strip()
    sort = request.args.get('sort', 'id')
    order = request.args.get('order', 'asc')

    conn = get_db()
    all_tables = get_all_tables(conn)

    if not all_tables:
        conn.close()
        return "No tables found in database", 404

    default_table = all_tables[0]
    table = request.args.get('table', default_table)
    if table not in all_tables:
        table = default_table

    columns = get_columns(conn, table)
    col_names = [c.name for c in columns]
    dropdown_fields = TABLE_CONFIG.get(table, {}).get('dropdown_fields', {})

    if order not in ('asc', 'desc'):
        order = 'asc'
    if sort not in col_names:
        sort = 'id' if 'id' in col_names else col_names[0]

    total = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]

    if q:
        text_cols = [c.name for c in columns if c.name != 'id']
        like_clauses = ' OR '.join(f'"{c}" LIKE ?' for c in text_cols)
        params = [f'%{q}%'] * len(text_cols)
        rows = conn.execute(
            f'SELECT * FROM "{table}" WHERE {like_clauses} ORDER BY "{sort}" {order}',
            params
        ).fetchall()
    else:
        rows = conn.execute(
            f'SELECT * FROM "{table}" ORDER BY "{sort}" {order}'
        ).fetchall()

    result_paths = {}
    if 'results_path' in all_tables:
        rp_rows = conn.execute('SELECT * FROM results_path').fetchall()
        for rp in rp_rows:
            result_paths[rp['project_name']] = dict(rp)

    conn.close()
    return render_template_string(
        HTML,
        rows=rows, total=total, table=table,
        all_tables=all_tables, columns=columns,
        dropdown_fields=dropdown_fields,
        result_path_map=RESULT_PATH_MAP,
        result_paths=result_paths,
        msg=msg, q=q, sort=sort, order=order,
    )

@app.route('/add', methods=['POST'])
def add():
    table = request.form['table']
    conn = get_db()
    all_tables = get_all_tables(conn)
    if table not in all_tables:
        conn.close()
        return "Unknown table", 400

    columns = get_columns(conn, table)
    fields = [c.name for c in columns if c.name != 'id']
    values = [request.form.get(f, '') for f in fields]
    placeholders = ', '.join('?' * len(fields))
    cols = ', '.join(f'"{f}"' for f in fields)
    conn.execute(f'INSERT INTO "{table}" ({cols}) VALUES ({placeholders})', values)
    conn.commit()
    conn.close()
    return redirect(url_for('index', table=table, msg='Row added'))

@app.route('/update', methods=['POST'])
def update():
    table = request.form['table']
    row_id = request.form['id']
    q = request.form.get('q', '')
    sort = request.form.get('sort', 'id')
    order = request.form.get('order', 'asc')

    conn = get_db()
    all_tables = get_all_tables(conn)
    if table not in all_tables:
        conn.close()
        return "Unknown table", 400

    columns = get_columns(conn, table)
    fields = [c.name for c in columns if c.name != 'id']
    sets = ', '.join(f'"{f}" = ?' for f in fields)
    values = [request.form.get(f, '') for f in fields]
    values.append(row_id)
    conn.execute(f'UPDATE "{table}" SET {sets} WHERE id = ?', values)
    conn.commit()
    conn.close()
    return redirect(url_for('index', table=table, msg='Saved', q=q, sort=sort, order=order))

@app.route('/delete/<int:row_id>')
def delete(row_id):
    table = request.args.get('table', '')
    q = request.args.get('q', '')
    sort = request.args.get('sort', 'id')
    order = request.args.get('order', 'asc')

    conn = get_db()
    all_tables = get_all_tables(conn)
    if table not in all_tables:
        conn.close()
        return "Unknown table", 400

    conn.execute(f'DELETE FROM "{table}" WHERE id = ?', (row_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index', table=table, msg='Deleted', q=q, sort=sort, order=order))

# =============================================================================
# REST API ДЛЯ ВОРКЕРА
# =============================================================================

@app.route('/api/next_step', methods=['GET'])
def api_next_step():
    try:
        with get_db() as conn:
            rows = conn.execute("""
                SELECT id, project_name, path_to_code, path_to_buildography
                FROM status
                WHERE project_name IS NOT NULL AND project_name != ''
                  AND path_to_code  IS NOT NULL AND path_to_code  != ''
                ORDER BY id ASC
            """).fetchall()

            for row in rows:
                project_id   = row['id']
                project_name = row['project_name']
                path_to_code = row['path_to_code']

                has_src = os.path.isdir(os.path.join(path_to_code, 'src'))
                has_bin = os.path.isdir(os.path.join(path_to_code, 'bin'))
                if not has_src and not has_bin:
                    logger.warning(
                        "Проект '%s' (id=%s): в '%s' нет директорий src и bin — пропускаем",
                        project_name, project_id, path_to_code
                    )
                    continue

                statuses = conn.execute(
                    "SELECT * FROM status WHERE id = ?", (project_id,)
                ).fetchone()
                if not statuses:
                    continue
                status_dict = dict(statuses)

                for step in STEPS_IN_ORDER:
                    if step not in status_dict:
                        continue
                    if status_dict[step] != 'NOT_STARTED':
                        continue

                    deps_ok = all(
                        status_dict.get(dep) == 'SUCCEEDED'
                        for dep in STEP_DEPENDENCIES.get(step, [])
                    )
                    if not deps_ok:
                        continue

                    if step == 'status_buildography_analyze':
                        if not row['path_to_buildography']:
                            logger.info(
                                "Проект '%s': path_to_buildography не задан — пропускаем %s",
                                project_name, step
                            )
                            continue

                    cursor = conn.execute(
                        f"UPDATE status SET {step} = 'PROCESSING' "
                        f"WHERE id = ? AND {step} = 'NOT_STARTED'",
                        (project_id,)
                    )
                    conn.commit()
                    if cursor.rowcount == 0:
                        logger.info(
                            "Проект '%s', шаг '%s' уже взят другим воркером",
                            project_name, step
                        )
                        continue

                    logger.info(
                        "Выдаём задачу: project='%s' (id=%s), step='%s'",
                        project_name, project_id, step
                    )
                    return jsonify({
                        'project_id':           project_id,
                        'project_name':         project_name,
                        'step':                 step,
                        'path_to_code':         path_to_code,
                        'path_to_buildography': row['path_to_buildography'] or "",
                        'has_src':              has_src,
                        'has_bin':              has_bin,
                    })

        return jsonify({'step': None})

    except Exception as e:
        logger.exception("Ошибка в api_next_step: %s", e)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/update_step', methods=['POST'])
def api_update_step():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid or missing JSON body'}), 400

    project_id   = data.get('project_id')
    project_name = data.get('project_name')
    step         = data.get('step')
    new_status   = data.get('status')
    result_path  = data.get('result_path', '')

    if not step or not new_status:
        return jsonify({'error': 'Missing required fields: step, status'}), 400

    if not project_id and not project_name:
        return jsonify({'error': 'Missing required fields: project_id or project_name'}), 400

    if step not in ALLOWED_STEPS:
        logger.warning("Попытка передать недопустимый step='%s'", step)
        return jsonify({'error': f'Unknown step: {step}'}), 400

    allowed_statuses = {'SUCCEEDED', 'FAILED', 'NOT_STARTED', 'PROCESSING'}
    if new_status not in allowed_statuses:
        return jsonify({'error': f'Invalid status: {new_status}'}), 400

    try:
        with get_db() as conn:
            if project_id:
                project = conn.execute(
                    "SELECT id, project_name FROM status WHERE id = ?", (project_id,)
                ).fetchone()
                if not project:
                    return jsonify({'error': f'Project not found by id={project_id}'}), 404
            else:
                project = conn.execute(
                    "SELECT id, project_name FROM status WHERE project_name = ?", (project_name,)
                ).fetchone()
                if not project:
                    return jsonify({'error': f'Project not found by name={project_name}'}), 404

            pid  = project['id']
            pname = project['project_name']

            conn.execute(
                f"UPDATE status SET {step} = ? WHERE id = ?",
                (new_status, pid)
            )
            conn.commit()
            logger.info("Обновлён статус: project='%s' (id=%s), step='%s' -> '%s'",
                        pname, pid, step, new_status)

            if new_status == 'SUCCEEDED' and result_path:
                path_field = RESULT_PATH_MAP.get(step)
                if path_field:
                    if path_field not in ALLOWED_PATH_FIELDS:
                        logger.error("Недопустимое path_field='%s' для step='%s'", path_field, step)
                        return jsonify({'error': 'Internal mapping error'}), 500

                    existing = conn.execute(
                        "SELECT id FROM results_path WHERE project_name = ?", (pname,)
                    ).fetchone()
                    if existing:
                        conn.execute(
                            f"UPDATE results_path SET {path_field} = ? WHERE project_name = ?",
                            (result_path, pname)
                        )
                    else:
                        conn.execute(
                            f"INSERT INTO results_path (project_name, {path_field}) VALUES (?, ?)",
                            (pname, result_path)
                        )
                    conn.commit()
                    logger.info("Сохранён путь: project='%s', %s='%s'", pname, path_field, result_path)

        return jsonify({'status': 'ok', 'updated': step})

    except Exception as e:
        logger.exception("Ошибка в api_update_step: %s", e)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/status_overview', methods=['GET'])
def api_status_overview():
    try:
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM status WHERE project_name IS NOT NULL AND project_name != ''"
            ).fetchall()

        summary = []
        for row in rows:
            d = dict(row)
            counts = {'NOT_STARTED': 0, 'PROCESSING': 0, 'SUCCEEDED': 0, 'FAILED': 0}
            for step in STEPS_IN_ORDER:
                val = d.get(step)
                if val in counts:
                    counts[val] += 1
            summary.append({
                'project_id':   d['id'],
                'project_name': d['project_name'],
                'counts':       counts,
            })
        return jsonify(summary)

    except Exception as e:
        logger.exception("Ошибка в api_status_overview: %s", e)
        return jsonify({'error': 'Internal server error'}), 500

# -----------------------------------------------------------------------------
# ЗАПУСК ПРИЛОЖЕНИЯ
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    logger.info("Запуск Flask на %s:%s (debug=%s)", host, port, debug)
    app.run(host=host, port=port, debug=debug)