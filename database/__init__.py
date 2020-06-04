import sqlite3
import json
import sys 

"""
Database will be removed when mqttdevices works properly
Target v2.0.0
"""

db = sqlite3.connect(f"{sys.path[0]}/config/tuyamqtt.db", check_same_thread=False)
cursor = db.cursor()


def disconnect():
    db.close()


def setup():

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY, 
            deviceid TEXT unique,
            localkey TEXT, 
            ip TEXT, 
            protocol TEXT, 
            topic TEXT, 
            attributes TEXT, 
            status_poll FLOAT, 
            status_command INTEGER
            hass_discover BOOL,
            name TEXT
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS attributes (
            id INTEGER PRIMARY KEY, 
            entity_id INTEGER,
            dpsitem INTEGER,
            dpsvalue FLOAT,
            dpstype TEXT,
            via TEXT
        )
    """
    )

    db.commit()


# quick and dirty


def get_entities():

    dictOfEntities = {}
    cursor.execute("""SELECT * FROM entities""")
    all_rows = cursor.fetchall()
    for row in all_rows:

        entity = {
            "id": row[0],
            "deviceid": row[1],
            "localkey": row[2],
            "ip": row[3],
            "protocol": row[4],            
            "attributes": json.loads(row[6]),
            "topic_config": True,
        }
        dictOfEntities[row[1]] = entity
    # print(dictOfEntities)
    return dictOfEntities


def attributes_to_json(entity: dict):

    dbentity = dict(entity)
    dbentity["attributes"] = json.dumps(dbentity["attributes"])
    return dbentity


def insert_entity(entity: dict):
   
    if not entity["topic_config"]:
        return False

    try:
        cursor.execute(
            """INSERT INTO entities(deviceid, localkey, ip, protocol, attributes)
                        VALUES(:deviceid, :localkey, :ip, :protocol, :attributes)""",
            attributes_to_json(entity),
        )
        db.commit()
        entity["id"] = cursor.lastrowid
    except Exception as e:
        # print(e)
        db.rollback()
        return False

    return True
    # insert attributes
    # db.commit()


def update_entity(entity: dict):

    if not entity["topic_config"]:
        return False

    try:
        with db:
            db.execute(
                """UPDATE entities 
                    SET deviceid = ?, localkey = ?, ip = ?, protocol = ?,  attributes = ?
                    WHERE id = ?""",
                (
                    entity["deviceid"],
                    entity["localkey"],
                    entity["ip"],
                    entity["protocol"],
                    json.dumps(entity["attributes"]),
                    entity["id"],
                ),
            )
    except Exception as e:
        # print(e)
        return False
    return True


def upsert_entity(entity: dict):

    if not entity["topic_config"]:
        return False

    if not insert_entity(entity):
        return update_entity(entity)


def upsert_entities(entities: dict):

    if False in set(map(upsert_entity, entities.values())):
        return False
    return True


def delete_entity(entity: dict):

    if "id" not in entity:
        return

    cursor.execute("""DELETE FROM entities WHERE id = ? """, (entity["id"],))
    # delete attributes
    db.commit()
