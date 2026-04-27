import sqlite3

db = sqlite3.connect('main-table-project.db')

#Create Cursor
Cursor = db.cursor()

Cursor.execute("""CREATE TABLE status (
               name text,
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

db.commit()

db.close()