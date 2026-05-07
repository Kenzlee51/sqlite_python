import sqlite3

db = sqlite3.connect('main-table-project.db')

#Create Cursor
Cursor = db.cursor()

#Основная таблица со статусами по преоктам. Тут добавляются 
# новые преокты для анализа и определяется статус для всех 
# последующих шагов анализа
Cursor.execute("""CREATE TABLE status (
               id integer PRIMARY KEY AUTOINCREMENT,
               project_name text,
               status_keep_unpacked text,
               path_to_code text,
               json_src_bin_path text,
               path_to_buildography text,
               status_unpacking text,
               status_json_src text,
               status_json_bin text,
               status_extensions text,
               status_binaries_in_src text,
               status_SQ text,
               status_svace_ob_build text,
               status_svace_ob_analyze text,
               status_svace_b_build text,
               status_svace_b_build_analyze text,
               status_buildography_analyze text,
               status_izb text,
               status_NOP_PREBUILD text,
               path_to_NOPBUILD text,
               status_NOP_POSTBUILD text,
               status_AKVS text,
               status_understand text,
               status_hash text,
               status_work text
                )""")

# Таблица-зеркало для таблицы status. Содержит в себе отражение 
# выполненных действий. Когда воркер берет в работу проект, в 
# таблице-зеркале появляется запись аналогичная основной таблице. 
# При обновлении статусов в основной таблцие воркер обнвовляет их и в зеркале.
# При внесении изменений в основную таблицу, вотчер увидит расхождения 
# между основной и зеркалом и запустит воркер с соответсвующими шагами

Cursor.execute("""CREATE TABLE status_mirror (
               id integer PRIMARY KEY AUTOINCREMENT,
               project_name text,
               status_keep_unpacked text,
               path_to_code text,
               json_src_bin_path text,
               path_to_buildography text,
               status_unpacking text,
               status_json_src text,
               status_json_bin text,
               status_extensions text,
               status_binaries_in_src text,
               status_SQ text,
               status_svace_ob_build text,
               status_svace_ob_analyze text,
               status_svace_b_build text,
               status_svace_b_build_analyze text,
               status_buildography_analyze text,
               status_izb text,
               status_NOP_PREBUILD text,
               path_to_NOPBUILD text,
               status_NOP_POSTBUILD text,
               status_AKVS text,
               status_understand text,
               status_hash text
               )""")

# ТАблица хранит в себе пути, по которым 
# лежат результаты шагов испытаний проведенных воркером
Cursor.execute("""CREATE TABLE results_path (
               id integer PRIMARY KEY AUTOINCREMENT,
               project_name text,
               json_src_bin_path text,
               keep_unpacked_path text,
               extensions_path text,
               binsrc_path text,
               SQ_result_path text,
               svace_ob_build_path text,
               svace_ob_analyze_path text,
               svace_b_build_path text,
               svace_b_analyze_path text,
               buildography_analyze_path text,
               path_nop_prebuild text,
               path_nop_postbuild text,
               understand_path text,
               izb_path text,
               AKVS_path text,
               hash_path text
               )""")

Cursor.execute("""CREATE TABLE statistics (
               id integer PRIMARY KEY AUTOINCREMENT,
               project_name text,
               languages text,
               izb_count integer,
               binsrc_count integer,
               svace_critical_count integer,
               svace_major_count integer,
               SQ_hotspots_count integer
               )""")

db.commit()

db.close()