import sqlite3

db = sqlite3.connect('main-table-project.db')

#Create Cursor
Cursor = db.cursor()

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
               status_hash text
                )""")

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