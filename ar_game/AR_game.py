import cv2
import numpy as np
import pyglet
from PIL import Image
import sys
import cv2.aruco as aruco
import random
import time

video_id = 0

if len(sys.argv) > 1:
    video_id = int(sys.argv[1])

# Create a video capture object for the webcam
cap = cv2.VideoCapture(video_id)

CAMERA_WIDTH = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
CAMERA_HEIGHT = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Fallback if the camera does not report a valid size
if CAMERA_WIDTH <= 0 or CAMERA_HEIGHT <= 0:
    CAMERA_WIDTH, CAMERA_HEIGHT = 640, 480

# Define the window size to be slightly larger than the camera feed to accommodate UI elements
WINDOW_WIDTH, WINDOW_HEIGHT = CAMERA_WIDTH + 200, CAMERA_HEIGHT + 200

window = pyglet.window.Window(WINDOW_WIDTH, WINDOW_HEIGHT)

game_title = "ITT - AR Game"
title = pyglet.text.Label(game_title, font_name="Arial", font_size=36, x=window.width//2, y=window.height - 50, anchor_x="center", anchor_y="center", color=(0, 0, 255, 200))

explanation_text_1 = "Use your finger to hit the targets on the screen."
explanation_text_2 = "Try to get the highest score possible in 30 seconds!"
explanation_text_3 = "Press SPACE to start the game!"
explanation_text_4 = "Press R to reset the game!"
explanation_text_5 = "Press Q to quit!"
explanation_1 = pyglet.text.Label(explanation_text_1, font_name="Arial", font_size=18, x=window.width//2, y=window.height//2 + 30, anchor_x="center", anchor_y="center", color=(0, 0, 255, 200))
explanation_2 = pyglet.text.Label(explanation_text_2, font_name="Arial", font_size=18, x=window.width//2, y=window.height//2, anchor_x="center", anchor_y="center", color=(0, 0, 255, 200))
explanation_3 = pyglet.text.Label(explanation_text_3, font_name="Arial", font_size=18, x=window.width//2, y=window.height//2 - 60, anchor_x="center", anchor_y="center", color=(0, 0, 255, 200))
explanation_4 = pyglet.text.Label(explanation_text_4, font_name="Arial", font_size=18, x=window.width//2, y=window.height//2 - 90, anchor_x="center", anchor_y="center", color=(0, 0, 255, 200))
explanation_5 = pyglet.text.Label(explanation_text_5, font_name="Arial", font_size=18, x=window.width//2, y=window.height//2 - 120, anchor_x="center", anchor_y="center", color=(0, 0, 255, 200))

final_label = final_label = pyglet.text.Label(f"Time up! Final score:", font_name="Arial", font_size=30, x=window.width // 2, y=window.height // 2, anchor_x="center", anchor_y="center", color=(0, 0, 255, 200) )

score_text = "Score: 0"
score_label = pyglet.text.Label(score_text, font_name="Arial", font_size=24, x=10, y=window.height - 30, anchor_x="left", anchor_y="center", color=(0, 0, 255, 200))

time_text = "Time left: 30s"
time_label = pyglet.text.Label(time_text, font_name="Arial", font_size=24, x=window.width - 10, y=window.height - 30, anchor_x="right", anchor_y="center", color=(0, 0, 255, 200))

background_color = (137, 137, 137, 255)
background = pyglet.image.SolidColorImagePattern(background_color).create_image(WINDOW_WIDTH, WINDOW_HEIGHT)

aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
aruco_params = aruco.DetectorParameters()
detector = aruco.ArucoDetector(aruco_dict, aruco_params)

last_good_warp = None

game_started = False
game_over = False
game_start_time = None
game_duration = 30

target_x, target_y = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
target_radius = 30
score = 0

# converts OpenCV image to PIL image and then to pyglet texture
# https://gist.github.com/nkymut/1cb40ea6ae4de0cf9ded7332f1ca0d55
def cv2glet(img,fmt):
    '''Assumes image is in BGR color space. Returns a pyimg object'''
    if fmt == 'GRAY':
      rows, cols = img.shape
      channels = 1
    else:
      rows, cols, channels = img.shape

    raw_img = Image.fromarray(img).tobytes()

    top_to_bottom_flag = -1
    bytes_per_row = channels*cols
    pyimg = pyglet.image.ImageData(width=cols, 
                                   height=rows, 
                                   fmt=fmt, 
                                   data=raw_img, 
                                   pitch=top_to_bottom_flag*bytes_per_row)
    return pyimg

# Returns the corner of the marker based on the role
def marker_corner(marker, role):
    pts = marker[0]

    if role == "tl":
        return pts[np.argmin(pts.sum(axis=1))]
    if role == "tr":
        return pts[np.argmax(pts[:, 0] - pts[:, 1])]
    if role == "br":
        return pts[np.argmax(pts.sum(axis=1))]
    if role == "bl":
        return pts[np.argmin(pts[:, 0] - pts[:, 1])]

def redraw_warped(corners, ids, frame):
    global last_good_warp

    # Check if we have detected 4 markers
    if ids is None or len(ids) != 4:
        return last_good_warp

    # Build list of markers with their center points
    markers = [(marker, marker[0].mean(axis=0)) for marker in corners]
    
    # Sort markers by y-coordinate
    markers = sorted(markers, key=lambda item: item[1][1])
    
    # Separate top and bottom markers, then sort by x-coordinate
    top_markers = sorted(markers[:2], key=lambda item: item[1][0])
    bottom_markers = sorted(markers[2:], key=lambda item: item[1][0])

    # Now we have the markers in order
    top_left_marker = top_markers[0][0]
    top_right_marker = top_markers[1][0]
    bottom_left_marker = bottom_markers[0][0]
    bottom_right_marker = bottom_markers[1][0]

    # Use marker_corner function to find e.g. top-left corner with 
    # similar logic as the order_points function
    src_points = np.float32([
        marker_corner(top_left_marker, "br"),
        marker_corner(top_right_marker, "bl"),
        marker_corner(bottom_right_marker, "tl"),
        marker_corner(bottom_left_marker, "tr"),
    ])

    dst_points = np.float32([
        [0, 0],
        [CAMERA_WIDTH - 1, 0],
        [CAMERA_WIDTH - 1, CAMERA_HEIGHT - 1],
        [0, CAMERA_HEIGHT - 1],
    ])

    # Calculate the perspective transformation matrix and warp the image
    M = cv2.getPerspectiveTransform(src_points, dst_points)
    warped = cv2.warpPerspective(frame, M, (CAMERA_WIDTH, CAMERA_HEIGHT))
    last_good_warp = warped
    return warped   

def track_finger(frame):
    global target_x, target_y, target_radius, score
    
    # Draw target circle
    cv2.circle(frame, (target_x, target_y), target_radius, (0, 255, 255), 2)
    
    # Blur to reduce noise
    blurred = cv2.GaussianBlur(frame, (11, 11), 0)
    
    # Convert to HSV color space
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    
    # Define skin color range in HSV
    lower_skin = np.array([0, 40, 60])
    upper_skin = np.array([20, 255, 255])
    
    # Create a binary mask where skin colors are white and the rest is black
    mask = cv2.inRange(hsv, lower_skin, upper_skin)
    
    # Clean up the mask
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    
    # Find contours in the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest_contour) > 1000:
            x, y, w, h = cv2.boundingRect(largest_contour)
            
            # Calculate distances from bounding box 
            top_dist = y
            bottom_dist= CAMERA_HEIGHT - (y + h)
            left_dist = x
            right_dist = CAMERA_WIDTH - (x + w)
            
            # Get min distance
            min_dist = min(top_dist, bottom_dist, left_dist, right_dist)
            
            # Get the corresponding corner based on the min distance
            top = tuple(largest_contour[largest_contour[:, :, 1].argmin()][0])
            bottom = tuple(largest_contour[largest_contour[:, :, 1].argmax()][0])
            right = tuple(largest_contour[largest_contour[:, :, 0].argmax()][0])
            left = tuple(largest_contour[largest_contour[:, :, 0].argmin()][0])
            
            # Depending on which side is closest, the opposite is the element to track
            if min_dist == bottom_dist:
                px, py = top[0], top[1]
            elif min_dist == top_dist:
                px, py = bottom[0], bottom[1]
            elif min_dist == left_dist:
                px, py = right[0], right[1]
            else:
                px, py = left[0], left[1]
              
            # Draw a circle on the detected fingertip  
            cv2.circle(frame, (px, py), 10, (0, 255, 0), -1)
            
            # Calculate distance from the target
            distance = np.sqrt((px - target_x)**2 + (py - target_y)**2)
            
            # If the distance is within the target radius, consider it a hit and move the target
            if distance < (target_radius + 10):
                cv2.circle(frame, (target_x, target_y), target_radius, (0, 0, 255), 2)
                score += 1
                target_x = random.randint(50, CAMERA_WIDTH - 50)
                target_y = random.randint(50, CAMERA_HEIGHT - 50)
                target_radius = random.randint(10, 40)
                
@window.event
def on_key_press(symbol, modifiers):
    global game_started, score, target_x, target_y, target_radius, game_over, game_start_time
    
    # Handle key press for starting
    if symbol == pyglet.window.key.SPACE:
        game_started = True
        game_over = False
        score = 0
        target_x = random.randint(50, CAMERA_WIDTH - 50)
        target_y = random.randint(50, CAMERA_HEIGHT - 50)
        target_radius = random.randint(10, 40)
        game_start_time = time.time()
        
    # Handle key press for quitting
    if symbol == pyglet.window.key.Q:
        pyglet.app.exit()
    
    # Handle key press for resetting the game
    if symbol == pyglet.window.key.R:
        game_started = False
        score = 0
        target_x, target_y = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
        target_radius = 30
        game_over = False
        game_start_time = None

@window.event
def on_draw():
    global game_started, score, target_x, target_y, target_radius, game_over, game_start_time
    
    window.clear()
    
    background.blit(0, 0, 0)
    title.draw()

    if game_started:
        elapsed = time.time() - game_start_time
        remaining = max(0, game_duration - int(elapsed))

        score_label.text = f"Score: {score}"
        score_label.draw()
        
        time_label.text = f"Time left: {remaining}s"
        time_label.draw()

        if elapsed >= game_duration:
            game_started = False
            game_over = True
        
        ret, frame = cap.read()
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, rejectedImgPoints = detector.detectMarkers(gray)
        
        # If we have detected 4 markers, draw the detected markers and warp the image. 
        # Otherwise, use the last good warp if it exists, or just show the original frame.
        if ids is not None and len(ids) == 4:
            aruco.drawDetectedMarkers(frame, corners)
            warped_img = redraw_warped(corners, ids, frame)
            track_finger(warped_img)
        else:
            warped_img = last_good_warp if last_good_warp is not None else frame
        
        img = cv2glet(warped_img, "BGR")
        img.blit(100, 100, 0)
    elif game_over:
        final_label.text = f"Time's up! Final score: {score}"
        explanation_4.draw()
        explanation_5.draw()
        final_label.draw()
    else:
        explanation_1.draw()
        explanation_2.draw()
        explanation_3.draw()
        explanation_4.draw()
        explanation_5.draw()

        

try:
    pyglet.app.run()
except KeyboardInterrupt:
    cap.release()
    cv2.destroyAllWindows()
    pyglet.app.exit()