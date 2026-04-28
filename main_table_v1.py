import sqlite3

db = sqlite3.connect('main-table-project.db')

#Create Cursor
Cursor = db.cursor()

Cursor.execute("""CREATE TABLE status (
               id integer PRIMARY KEY AUTOINCREMENT,
               project_name text,
               path_to_code text,
               path_to_buildography text,
               status_unpacking text,
               status_extensions text,
               status_binaries_in_src text,
               status_SQ text,
               status_svace_ob_build text,
               status_svace_ob_analyze text,
               status_svace_b_build text,
               status_svace_b_build_analyze text,
               status_buildography_analyze text,
               status_izb text,
               status_AKVS text,
               status_hash text
                )""")

Cursor.execute("""CREATE TABLE results_path (
               id integer PRIMARY KEY AUTOINCREMENT,
               project_name text,
               extensions_path text,
               binsrc_path text,
               SQ_result_path text,
               svace_ob_build_path text,
               svace_ob_analyze_path text,
               svace_b_build_path text,
               svace_b_analyze_path text,
               buildography_analyze_path text,
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