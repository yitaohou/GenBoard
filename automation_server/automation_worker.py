import pyautogui
import time
import sys
import json

def set_climb_on_board(holds):
    """
    Simulates mouse clicks on the screen to set a climb on the Kilter Board app.

    Args:
        holds (list): A list of dictionaries, where each dictionary represents a hold
                      and contains 'row_num' and 'col_num'.
    """
    print("Starting automation...")
    print("Received holds:", holds)

    # --- CALIBRATION NEEDED ---
    # You must manually find the pixel coordinates for the top-left and bottom-right
    # points of the Kilter Board grid in your emulator.
    # Use a screenshot and an image editor to find these pixel values.
    # For example, on a 1920x1080 screen, these might be:
    TOP_LEFT_X = 500  # Placeholder: X-coordinate of the center of the top-left-most hold
    TOP_LEFT_Y = 200  # Placeholder: Y-coordinate of the center of the top-left-most hold
    
    # These values represent the horizontal and vertical distance between adjacent holds.
    HORIZONTAL_SPACING = 40  # Placeholder: Pixels between columns
    VERTICAL_SPACING = 40    # Placeholder: Pixels between rows
    # --- END CALIBRATION ---

    # Give yourself a few seconds to switch to the emulator window
    # print("You have 5 seconds to focus the emulator window...")
    # time.sleep(5)

    # pyautogui.moveTo(100, 200, duration=1)

    for hold in holds:
        if 'row_num' in hold and 'col_num' in hold:
            # Calculate the pixel coordinates for the click
            # This assumes a simple grid. You may need to adjust this logic based on
            # the actual layout of the holds (e.g., for staggered 'small' holds).
            pixel_x = TOP_LEFT_X + (hold['col_num'] * HORIZONTAL_SPACING)
            pixel_y = TOP_LEFT_Y + (hold['row_num'] * VERTICAL_SPACING)

            print(f"Moving to hold: row {hold['row_num']}, col {hold['col_num']} at ({pixel_x}, {pixel_y})")
            
            # Perform the mouse move
            pyautogui.click(pixel_x, pixel_y, duration=0.01)
            
            # We'll keep a small delay to make the overall path clear
            time.sleep(0.1)

    print("Automation complete.")

if __name__ == '__main__':
    # This allows us to run the script directly for testing.
    # It reads hold data from the command line arguments.
    if len(sys.argv) > 1:
        # The climb data is passed as a JSON string
        climb_data_str = sys.argv[1]
        climb_data = json.loads(climb_data_str)
        set_climb_on_board(climb_data.get('holds', []))
    else:
        print("No climb data provided. To test, run: python3 automation_worker.py '<json_data>'")
