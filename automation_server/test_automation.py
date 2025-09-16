import pyautogui
import time

# Give a moment to see the initial position
time.sleep(2)

print("Moving mouse to (100, 200)...")
# Move the mouse to coordinates (100, 200) over 1 second
pyautogui.moveTo(100, 200, duration=1)

# Click at the current mouse position
pyautogui.click()
print("Clicked at (100, 200).")

# Get and print the current mouse position to confirm
current_position = pyautogui.position()
print(f"Current mouse position is: {current_position}")
