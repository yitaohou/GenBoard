import sqlite3
import json
import re
import collections

def parse_frames(frames_string, holes_map, roles_map):
    holds = []
    # The regex finds all occurrences of 'p' followed by digits (hole_id)
    # and 'r' followed by digits (role_id).
    pattern = re.compile(r'p(\d+)r(\d+)')
    matches = pattern.findall(frames_string)

    for hole_id, role_id in matches:
        hole_id = int(hole_id)
        role_id = int(role_id)
        
        hold_info = holes_map.get(hole_id)
        role_info = roles_map.get(role_id)

        if hold_info and role_info:
            holds.append({
                'hole_id': hole_id,
                'role_id': role_id,
                'x': hold_info['x'],
                'y': hold_info['y'],
                'x_db': hold_info['x_db'],
                'y_db': hold_info['y_db'],
                'role_name': role_info['name'],
                'role_color': role_info['screen_color']
            })
    return holds

def main():
    """
    Main function to connect to the database, parse the data, and export to JSON.
    """
    db_path = '../kilterboard.db'
    output_path = 'climbs.json'
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        print(f"Successfully connected to {db_path}")

        # --- Schema Exploration ---
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        db_schema = {}
        for table_name in tables:
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns_data = cursor.fetchall()
            columns = [
                {
                    'id': col[0],
                    'name': col[1],
                    'type': col[2],
                    'notnull': col[3],
                    'default_value': col[4],
                    'primary_key': col[5]
                }
                for col in columns_data
            ]
            db_schema[table_name] = columns

        # Write schema to JSON
        with open('schema.json', 'w') as f:
            json.dump(db_schema, f, indent=2)
        print("Successfully exported database schema to schema.json")

        # 1. Fetch filtered holes for product_id=1 and export to JSON
        cursor.execute("SELECT * FROM holes WHERE product_id = 1;")
        holes_data = cursor.fetchall()
        holes_list = [dict(row) for row in holes_data]
        
        # Sort the list of holes by 'id'
        holes_list.sort(key=lambda h: h['id'])

        print(f"Found {len(holes_list)} holes for product_id=1.")
        with open('holes.json', 'w') as f:
            json.dump(holes_list, f, indent=2)
        print("Successfully exported filtered holes data for product_id=1 to holes.json")
        
        # Create a map with x,y coordinates, parsing from the 'name' field
        holes_map = {}
        for h in holes_list:
            parts = h['name'].split(',')
            if len(parts) == 2:
                holes_map[h['id']] = {
                    'x': parts[0],      # Parsed string x
                    'y': parts[1],      # Parsed string y
                    'x_db': h['x'],     # Original int x
                    'y_db': h['y']      # Original int y
                }
        
        print(f"Created holes_map with {len(holes_map)} entries from 'name' field.")

        # --- Analysis: Calculate Hole Frequency ---
        valid_hole_ids = set(h['id'] for h in holes_list)
        
        # Fetch all climb frames for the relevant layout, filtering for popular climbs
        print("Starting hole frequency analysis on climbs with >100 ascents...")
        cursor.execute("""
            SELECT c.frames FROM climbs c
            JOIN climb_stats cs ON c.uuid = cs.climb_uuid
            WHERE c.layout_id = 1 AND c.is_listed = 1 AND c.is_draft = 0 AND cs.ascensionist_count > 100;
        """)
        all_frames = cursor.fetchall()

        hole_frequency = collections.Counter()
        frame_pattern = re.compile(r'p(\d+)r(\d+)')
        for frame_data in all_frames:
            matches = frame_pattern.findall(frame_data['frames'])
            for hole_id, role_id in matches:
                hole_frequency[int(hole_id)] += 1
        
        # Filter the frequency counter to only include our valid holes
        filtered_frequency = {
            hole_id: count for hole_id, count in hole_frequency.items()
            if hole_id in valid_hole_ids
        }
        
        # Sort the dictionary by frequency (value) in descending order
        sorted_frequency = dict(sorted(filtered_frequency.items(), key=lambda item: item[1], reverse=True))
        
        # Export the frequency data to JSON
        with open('hole_frequency.json', 'w') as f:
            json.dump(sorted_frequency, f, indent=2)
        
        print(f"Analysis complete. Exported usage frequency for {len(sorted_frequency)} holes to hole_frequency.json.")
        # --- End of Analysis ---

        # 2. Fetch all placement roles for product_id=1 and export to JSON
        cursor.execute("SELECT * FROM placement_roles WHERE product_id = 1;")
        roles_data = cursor.fetchall()
        roles_list = [dict(row) for row in roles_data]
        with open('roles.json', 'w') as f:
            json.dump(roles_list, f, indent=2)
        print("Successfully exported placement roles data for product_id=1 to roles.json")
        roles_map = {r['id']: {'name': r['name'], 'screen_color': r['screen_color']} for r in roles_list}

        # 3. Fetch climbs with their stats
        query = """
        SELECT
            c.uuid,
            c.layout_id,
            c.name,
            c.setter_username,
            c.description,
            c.frames,
            c.edge_left,
            c.edge_right,
            c.edge_bottom,
            c.edge_top,
            cs.angle,
            cs.display_difficulty,
            cs.ascensionist_count,
            cs.quality_average
        FROM
            climbs c
        JOIN
            climb_stats cs ON c.uuid = cs.climb_uuid
        WHERE c.is_listed = 1 AND c.is_draft = 0 AND c.layout_id = 1 AND cs.ascensionist_count > 100;
        """
        # we filter the most common layout
        cursor.execute(query)
        climbs_data = cursor.fetchall()
        print(f"Found {len(climbs_data)} listed climbs with >100 ascents.")
        
        all_climbs = []
        for climb in climbs_data:
            climb_dict = dict(climb)
            climb_dict['holds'] = parse_frames(climb['frames'], holes_map, roles_map)
            del climb_dict['frames'] # remove raw frames string
            all_climbs.append(climb_dict)

        # 4. Write to JSON
        with open(output_path, 'w') as f:
            json.dump(all_climbs, f, indent=2)
        print(f"Successfully exported data to {output_path}")

        # --- Export Raw Attributes for the Same Climbs ---
        print("\nExporting raw attributes for the filtered climbs...")
        raw_query = """
        SELECT
            c.*,
            cs.*
        FROM
            climbs c
        JOIN
            climb_stats cs ON c.uuid = cs.climb_uuid
        WHERE c.is_listed = 1 AND c.is_draft = 0 AND c.layout_id = 1 AND cs.ascensionist_count > 100;
        """
        cursor.execute(raw_query)
        raw_climbs_data = cursor.fetchall()
        raw_climbs_list = [dict(row) for row in raw_climbs_data]
        
        with open('climbs_raw_attributes.json', 'w') as f:
            json.dump(raw_climbs_list, f, indent=2)
        print("Successfully exported raw climb attributes to climbs_raw_attributes.json")
        # --- End of Raw Export ---

        # --- Create Climb Summary Export ---
        print("\nCreating a summary for the first 20 climbs...")
        climb_summary = []
        for climb in all_climbs[:20]:
            start_holds = [{'x': h['x'], 'y': h['y']} for h in climb['holds'] if h['role_name'] == 'start']
            finish_holds = [{'x': h['x'], 'y': h['y']} for h in climb['holds'] if h['role_name'] == 'finish']
            
            climb_summary.append({
                'name': climb['name'],
                'start_holds': start_holds,
                'finish_holds': finish_holds,
                'edge_left': climb['edge_left'],
                'edge_right': climb['edge_right'],
                'edge_bottom': climb['edge_bottom'],
                'edge_top': climb['edge_top']
            })
        
        with open('climb_summary.json', 'w') as f:
            json.dump(climb_summary, f, indent=2)
        print("Successfully exported climb summary to climb_summary.json")
        # --- End of Summary Export ---

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        # Make sure to close the connection
        if conn:
            conn.close()
            print("\nDatabase connection closed.")

if __name__ == '__main__':
    main()
