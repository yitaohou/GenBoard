import sqlite3
import json
import re

def parse_simplified_frames(frames_string):
    """
    Parses the raw frames string to extract a simplified list of holds.
    """
    holds = []
    pattern = re.compile(r'p(\d+)r(\d+)')
    matches = pattern.findall(frames_string)
    
    # We need a small, temporary map for role_ids to role_names for this script
    # This is a simplified version of what's in the main data_explorer
    roles_map = {
        12: 'start',
        13: 'middle',
        14: 'finish',
        15: 'foot'
    }

    for hole_id, role_id in matches:
        hole_id = int(hole_id)
        role_name = roles_map.get(int(role_id), 'unknown')
        
        hold_data = {
            'hole_id': hole_id,
            'role_name': role_name
        }
        
        # Add structural info for the 'large' hold set
        if 1090 <= hole_id <= 1395:
            # Calculate row and column based on 17 elements per row
            index = hole_id - 1090
            row_num = (index // 17) + 1 # Reverted from +2
            col_num = (index % 17) + 1
            
            hold_data['row_num'] = row_num
            hold_data['col_num'] = col_num
            hold_data['hold_type'] = 'large'
        
        # Add structural info for the 'small', staggered hold set
        elif 1465 <= hole_id <= 1599:
            index = hole_id - 1465
            row_idx = index // 9  # 0-indexed row
            col_idx = index % 9   # 0-indexed column in row
            
            # Row number starts at 1.5 and increases by 1
            hold_data['row_num'] = 1.5 + row_idx # Reverted from 2.5
            
            # Column number starts at 0.5 for even rows, 1.5 for odd rows
            start_col = 0.5 if row_idx % 2 == 0 else 1.5
            hold_data['col_num'] = start_col + (col_idx * 2)
            
            hold_data['hold_type'] = 'small'
        
        # Add structural info for the bottom row of holds
        elif 1073 <= hole_id <= 1089:
            hold_data['row_num'] = 0 # Reverted from 1
            # col_num is inversely related to hole_id in this range
            hold_data['col_num'] = 1089 - hole_id + 1
            hold_data['hold_type'] = 'bottom_row'
            
        # Add structural info for the top row of holds
        elif 1447 <= hole_id <= 1464:
            hold_data['row_num'] = -1 # Reverted from 0
            # col_num decreases from 17.5 to 0.5 in this range
            hold_data['col_num'] = 17.5 - (hole_id - 1447)
            hold_data['hold_type'] = 'top_row'

        holds.append(hold_data)

    return holds

def main():
    """
    Connects to the database, fetches popular climbs, de-duplicates them by name,
    and exports a simplified JSON file.
    """
    db_path = '../kilterboard.db'
    output_path = 'climb_data.json'
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        print(f"Successfully connected to {db_path}")

        # Fetch all climbs with more than 50 ascents
        query = """
        SELECT
            c.name,
            c.frames,
            cs.angle,
            cs.ascensionist_count
        FROM
            climbs c
        JOIN
            climb_stats cs ON c.uuid = cs.climb_uuid
        WHERE c.is_listed = 1 AND c.is_draft = 0 AND c.layout_id = 1 AND cs.ascensionist_count > 50;
        """
        cursor.execute(query)
        all_popular_climbs = cursor.fetchall()
        print(f"Found {len(all_popular_climbs)} climbs with >50 ascents.")

        # Process climbs to keep only the one with the highest ascent count for each name
        unique_climbs = {}
        for climb in all_popular_climbs:
            name = climb['name']
            if name not in unique_climbs or climb['ascensionist_count'] > unique_climbs[name]['ascensionist_count']:
                unique_climbs[name] = climb
        
        print(f"Filtered down to {len(unique_climbs)} unique climbs by name.")

        # Create the final simplified list
        simplified_data = []
        for climb in unique_climbs.values():
            simplified_data.append({
                'name': climb['name'],
                'angle': climb['angle'],
                'holds': parse_simplified_frames(climb['frames'])
            })

        # Write to JSON
        with open(output_path, 'w') as f:
            json.dump(simplified_data, f, indent=2)
        print(f"Successfully exported simplified data to {output_path}")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
            print("\nDatabase connection closed.")

if __name__ == '__main__':
    main()
