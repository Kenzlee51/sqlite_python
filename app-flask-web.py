# =============================================================================
# app.py — Flask-интерфейс для редактирования SQLite БД
# =============================================================================
#
# БЫСТРЫЙ СТАРТ:
#   1. Положите app.py рядом с вашим .db файлом
#   2. Укажите имя файла БД в DB_PATH ниже
#   3. pip install flask
#   4. python app.py
#   5. Откройте http://your-server:5000
#
# КАК РАБОТАЕТ БЕЗ КОНФИГА:
#   Все таблицы из БД подхватываются автоматически.
#   Типы полей определяются из схемы БД:
#     TEXT, VARCHAR, CHAR  → текстовый инпут
#     INTEGER, REAL        → числовой инпут
#   Полный функционал: просмотр, добавление, редактирование, удаление, поиск.
#
# КАК ДОБАВИТЬ ДРОПДАУНЫ (TABLE_CONFIG):
#   TABLE_CONFIG нужен только если хотите дропдауны для конкретных полей.
#   Таблицы не перечисленные в TABLE_CONFIG работают автоматически.
#
#   Структура записи:
#
#     'имя_таблицы': {
#         'dropdown_fields': {
#             'имя_поля': ['', 'вариант1', 'вариант2', ...],
#             #            ↑
#             #            пустая строка в начале = "не выбрано"
#         },
#     },
#
#   Пример с двумя таблицами:
#
#     TABLE_CONFIG = {
#         'tasks': {
#             'dropdown_fields': {
#                 'priority': ['', 'low', 'medium', 'high'],
#                 'status':   ['', 'todo', 'in_progress', 'done'],
#             },
#         },
#         'builds': {
#             'dropdown_fields': {
#                 'result': ['', 'success', 'failure', 'na'],
#                 'env':    ['', 'dev', 'staging', 'prod'],
#             },
#         },
#     }
#
#   Поля таблицы НЕ указанные в dropdown_fields рендерятся автоматически
#   по типу из БД — конфигурировать их не нужно.
#
# ПАРАЛЛЕЛЬНАЯ РАБОТА С SQLITE-WEB:
#   Flask и sqlite-web можно запускать одновременно на разных портах,
#   оба работают с одним файлом БД без конфликтов.
# =============================================================================

from flask import Flask, render_template_string, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Путь к файлу базы данных
DB_PATH = 'main-table-project.db'

# =============================================================================
# КОНФИГ ТАБЛИЦ
# Добавляйте сюда таблицы только если нужны дропдауны.
# Остальные таблицы работают автоматически без записи здесь.
# =============================================================================
TABLE_CONFIG = {

    # Таблица статусов сборки — все status_* поля как дропдауны
    'status': {
        'dropdown_fields': {
            'status_unpacking':             ['NOT_STARTED', 'SUCCEEDED', 'FAILED'],
            'status_extensions':            ['NOT_STARTED', 'SUCCEEDED', 'FAILED'],
            'status_binaries_in_src':       ['NOT_STARTED', 'SUCCEEDED', 'FAILED'],
            'status_SQ':                    ['NOT_STARTED', 'SUCCEEDED', 'FAILED'],
            'status_svace_ob_build':        ['NOT_STARTED', 'SUCCEEDED', 'FAILED'],
            'status_svace_ob_analyze':      ['NOT_STARTED', 'SUCCEEDED', 'FAILED'],
            'status_svace_b_build':         ['NOT_STARTED', 'SUCCEEDED', 'FAILED'],
            'status_svace_b_build_analyze': ['NOT_STARTED', 'SUCCEEDED', 'FAILED'],
            'status_buildography_analyze':  ['NOT_STARTED', 'SUCCEEDED', 'FAILED'],
            'status_izb':                   ['NOT_STARTED', 'SUCCEEDED', 'FAILED'],
            'status_understand':            ['NOT_STARTED', 'SUCCEEDED', 'FAILED'],
            'status_AKVS':                  ['NOT_STARTED', 'SUCCEEDED', 'FAILED'],
            'status_hash':                  ['NOT_STARTED', 'SUCCEEDED', 'FAILED']
        },
    },

    # Пример новой таблицы с дропдаунами — раскомментируйте и адаптируйте:
    # 'my_table': {
    #     'dropdown_fields': {
    #         'priority': ['', 'low', 'medium', 'high'],
    #         'env':      ['', 'dev', 'staging', 'prod'],
    #     },
    # },

}
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
    padding: 0.7rem 0.8rem; text-align: left; color: var(--muted);
    font-weight: 600; white-space: nowrap; font-size: 0.63rem;
    text-transform: uppercase; letter-spacing: 0.05em;
  }
  th.sortable { cursor: pointer; user-select: none; }
  th.sortable:hover { color: var(--text); }
  th.sort-asc::after  { content: ' ↑'; color: var(--accent); }
  th.sort-desc::after { content: ' ↓'; color: var(--accent); }

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
    font-size: 0.7rem; cursor: pointer; width: 90px;
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
              <select name="{{ col.name }}" class="inline {{ row[col.name] or '' }}"
                      onchange="this.className='inline '+this.value">
                {% for opt in dropdown_fields[col.name] %}
                <option value="{{ opt }}" {% if row[col.name]==opt %}selected{% endif %}>{{ opt or '—' }}</option>
                {% endfor %}
              </select>
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

<script>
function toggleAdd() {
  document.getElementById('addPanel').classList.toggle('open');
}
</script>
</body>
</html>
"""


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# Таблицы которые не показываются в интерфейсе
HIDDEN_TABLES = {'sqlite_sequence'}

def get_all_tables(conn):
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    return [r['name'] for r in rows if r['name'] not in HIDDEN_TABLES]


class ColInfo:
    def __init__(self, name, col_type):
        self.name = name
        self.type_upper = (col_type or 'TEXT').upper().split('(')[0].strip()


def get_columns(conn, table):
    rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    return [ColInfo(r['name'], r['type']) for r in rows]


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

    conn.close()
    return render_template_string(
        HTML,
        rows=rows, total=total, table=table,
        all_tables=all_tables, columns=columns,
        dropdown_fields=dropdown_fields,
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
