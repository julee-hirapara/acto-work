# import json
# import db_config_1 as db
#
# conn = db.get_db_connection(db.db_name)
#
# cursor = conn.cursor()
#
# # Read records
# cursor.execute("SELECT id, size_chart FROM data_052026_copy")
#
# rows = cursor.fetchall()
#
# for row in rows:
#
#     row_id = row['id']
#     size_chart = row['size_chart']
#
#     # skip NULL or empty values
#     if size_chart is None or size_chart == "":
#         print(f"Skipping ID {row_id} because size_chart is empty")
#         continue
#
#     try:
#         # convert string json to dict
#         data = json.loads(size_chart)
#
#         # process all groups
#         for group_key, group_values in data.items():
#
#             # skip if not dict
#             if not isinstance(group_values, dict):
#                 continue
#
#             for key, value in group_values.items():
#
#                 # only process string values containing |
#                 if isinstance(value, str) and "|" in value:
#
#                     # split and trim spaces
#                     group_values[key] = [
#                         item.strip()
#                         for item in value.split("|")
#                     ]
#
#         # convert back to json
#         updated_json = json.dumps(data)
#
#         # update table
#         update_query = """
#             UPDATE data_052026_copy
#             SET size_chart = %s
#             WHERE id = %s
#         """
#
#         cursor.execute(update_query, (updated_json, row_id))
#
#         print(f"Updated ID {row_id}")
#
#     except Exception as e:
#         print(f"Error in ID {row_id}: {e}")
#
# conn.commit()
#
# cursor.close()
# conn.close()
#
# print("Updated successfully")



import json
import db_config_1 as db

conn = db.get_db_connection(db.db_name)

cursor = conn.cursor()

# Recursive function
def convert_pipe_values(obj):

    # if dictionary
    if isinstance(obj, dict):

        for key, value in obj.items():

            # recursive call for nested dict/list
            obj[key] = convert_pipe_values(value)

    # if list
    elif isinstance(obj, list):

        obj = [convert_pipe_values(item) for item in obj]

    # if string containing pipe
    elif isinstance(obj, str) and "|" in obj:

        obj = [
            item.strip()
            for item in obj.split("|")
        ]

    return obj


# Read records
cursor.execute("SELECT hash_id, size_chart FROM data_052026_copy")

rows = cursor.fetchall()

for row in rows:

    row_id = row["hash_id"]
    size_chart = row["size_chart"]

    # skip empty values
    if not size_chart:
        continue

    try:

        # convert json string to python object
        data = json.loads(size_chart)

        # convert all pipe strings recursively
        updated_data = convert_pipe_values(data)

        # convert back to json
        updated_json = json.dumps(updated_data)

        # update db
        update_query = """
            UPDATE data_052026_copy
            SET size_chart = %s
            WHERE hash_id = %s
        """

        cursor.execute(update_query, (updated_json, row_id))

        print(f"Updated ID {row_id}")

    except Exception as e:

        print(f"Error in ID {row_id}: {e}")

conn.commit()

cursor.close()
conn.close()

print("All records updated successfully")