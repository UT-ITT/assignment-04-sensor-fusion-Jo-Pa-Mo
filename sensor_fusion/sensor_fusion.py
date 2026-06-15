import cv2
import numpy as np
import pyglet
from PIL import Image
import sys
import cv2.aruco as aruco
from DIPPID import SensorUDP
import os

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
alpha_label = pyglet.text.Label(f"Alpha: 0.5", font_name="Arial", font_size=18, x=10, y=10, anchor_x="left", anchor_y="bottom", color=(0, 0, 255, 200))

background_color = (137, 137, 137, 255)
background = pyglet.image.SolidColorImagePattern(background_color).create_image(WINDOW_WIDTH, WINDOW_HEIGHT)

aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
aruco_params = aruco.DetectorParameters()
detector = aruco.ArucoDetector(aruco_dict, aruco_params)

last_good_warp = None
M = None
accelerometer_data = None
alpha = 0.5
scale_factor = 50
prediction_x = CAMERA_WIDTH // 2
prediction_y = CAMERA_HEIGHT // 2

PORT = 5700
sensor = SensorUDP(PORT)

# Define callback function to handle incoming accelerometer data
def handle_accelerometer(data):
    global accelerometer_data
    accelerometer_data = data

# Button 1 to reset the prediction to the center of the camera feed
def handle_button_1(data):
    global prediction_x, prediction_y
    if data == 1:
        prediction_x = CAMERA_WIDTH // 2
        prediction_y = CAMERA_HEIGHT // 2

# Register the callback for accelerometer data
sensor.register_callback("accelerometer", handle_accelerometer)
sensor.register_callback("button_1", handle_button_1)

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
    global last_good_warp, M

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

@window.event
def on_key_press(symbol, modifiers):
    global alpha
    # Quit the application
    if symbol == pyglet.window.key.Q:
        os._exit(0)
    
    # Decrease alpha value
    if symbol == pyglet.window.key.LEFT:
        print("Left button pressed")
        alpha = max(-1, alpha - 0.1)
        
    # Increase alpha value
    if symbol == pyglet.window.key.RIGHT:
        print("Right button pressed")
        alpha = min(3, alpha + 0.1)


@window.event
def on_draw():
    global accelerometer_data, prediction_x, prediction_y
    #print("Accelerometer data:", accelerometer_data)
    
    window.clear()
    background.blit(0, 0, 0)
    alpha_label.text = f"Alpha: {alpha:.1f}"
    alpha_label.draw()

    ret, frame = cap.read()
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, rejectedImgPoints = detector.detectMarkers(gray)
    
    board_ids = {0, 1, 2, 3}
    
    # Check if we detected any markers and if they are part of our board
    if ids is not None:
        
        # flatten the ids array for easier processing
        detected = ids.flatten()
        board_corners = []
        board_marker_ids = []
        
        phone_center = None

        # Loop through detected markers and check if they are part of the board
        for corner, marker_id in zip(corners, detected):
            # If we detect the phone marker, save its center point
            if marker_id == 5:
                c = corner[0]
                phone_center = (
                    int(np.mean(c[:, 0])),
                    int(np.mean(c[:, 1]))
                )
            # If the marker is part of the board, save its corners and id for warping
            elif marker_id in board_ids:
                board_corners.append(corner)
                board_marker_ids.append(marker_id)

        # If we have detected all 4 markers of the board, draw them and warp the image
        if len(board_corners) == 4:
            aruco.drawDetectedMarkers(frame, board_corners)
            warped_img = redraw_warped(board_corners, np.array(board_marker_ids), frame)
        else:
            warped_img = last_good_warp if last_good_warp is not None else frame
    else:
        warped_img = last_good_warp if last_good_warp is not None else frame
      
    # If we have a warped image and a valid transformation matrix, we can apply sensor fusion to predict the phone's position  
    if warped_img is not None and M is not None:
        
        # Extract accelerometer data
        acc_x = accelerometer_data["x"] if accelerometer_data else 0
        acc_y = accelerometer_data["y"] if accelerometer_data else 0
        
        # Simple prediction based on accelerometer data
        prediction_x += acc_x * scale_factor
        prediction_y += acc_y * scale_factor
        
        # If we have a detected phone center, transform it to the warped image coordinates
        if phone_center is not None:
            
            # Transform the phone center point to the warped image coordinates using the perspective transformation matrix
            pt = np.array([[phone_center]], dtype=np.float32)
            warped_pt = cv2.perspectiveTransform(pt, M)[0][0]
            cam_x, cam_y = warped_pt[0], warped_pt[1]
            
            # Draw red circle
            cv2.circle(warped_img, (int(cam_x), int(cam_y)), 8, (0, 0, 255), -1)
            
            # Complementary Filter moves the prediction towards the camera measurement
            prediction_x = alpha * cam_x + (1 - alpha) * prediction_x
            prediction_y = alpha * cam_y + (1 - alpha) * prediction_y
        
        # Draw the predicted position as a green circle  
        cv2.circle(warped_img, (int(prediction_x), int(prediction_y)), 8, (0, 255, 0), -1)
            
    img = cv2glet(warped_img, "BGR")
    img.blit(100, 100, 0)

try:
    pyglet.app.run()
except KeyboardInterrupt:
    cap.release()
    cv2.destroyAllWindows()