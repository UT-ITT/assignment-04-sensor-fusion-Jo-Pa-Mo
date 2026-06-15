import argparse
import cv2
import numpy as np

WINDOW_NAME = 'Image Extractor'
points = []
base_img = None
img = None
x_resolution = 640
y_resolution = 480 

def redraw_warped():
    if len(points) == 4:
        # Define the source and destination points for perspective transformation
        # Source points are the selected points, and destination points are the corners of the output image
        # Source points need to be ordered so that they correspond to the destination points in the correct order 
        # (top-left, top-right, bottom-right, bottom-left)
        src_points = order_points(np.float32(points))
        dst_points = np.float32([[0, 0], [x_resolution, 0], [x_resolution, y_resolution], [0, y_resolution]])
        
        # Calculate the perspective transformation matrix
        M = cv2.getPerspectiveTransform(src_points, dst_points)
        
        # Apply the perspective transformation
        global img
        img = cv2.warpPerspective(base_img, M, (x_resolution, y_resolution))

def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    
    sum_pts = pts.sum(axis=1)
    diff_pts = np.diff(pts, axis=1)
    
    # Top-left
    rect[0] = pts[np.argmin(sum_pts)]
    
    # Bottom-right
    rect[2] = pts[np.argmax(sum_pts)]
    
    # Top-right
    rect[1] = pts[np.argmin(diff_pts)]
    
    # Bottom-left
    rect[3] = pts[np.argmax(diff_pts)]
    
    return rect

# Redraw the image with the selected points
def redraw():
    global img
    img = base_img.copy()
    
    cv2.putText(img, "Press 'ESC' to reset - Press 'S' to save - Press 'Q' to quit", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    
    # Draw circles on the selected points
    for x, y in points:
        img = cv2.circle(img, (x, y), 5, (255, 0, 0), -1)
        
    cv2.imshow(WINDOW_NAME, img)

# Mouse callback function to handle clicks and draw points
def mouse_callback(event, x, y, flags, param):
    global points
    
    # Check for left mouse button click
    if event == cv2.EVENT_LBUTTONDOWN:
        
        # Add the clicked point to the list if we have less than 4 points
        if len(points) < 4:
            points.append((x, y))
            redraw()
            
            # If we have 4 points, perform the perspective transformation and display the warped image
            if len(points) == 4:
                redraw_warped()
                cv2.imshow(WINDOW_NAME, img)

            
if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-path", type=str, default="./perspective_transformation/sample_image.jpg", help="Path to the input image")
    parser.add_argument("--output-path", type=str, default="./perspective_transformation/output/extracted_image.jpg", help="Path to save the extracted image")
    parser.add_argument("--x-resolution", type=int, default=640, help="Width of the output image")
    parser.add_argument("--y-resolution", type=int, default=480, help="Height of the output image")
    args = parser.parse_args()
    
    if args.x_resolution <= 0 or args.y_resolution <= 0:
        print("Error: x-resolution and y-resolution must be positive integers.")
        exit(1)
    else:
        x_resolution = args.x_resolution
        y_resolution = args.y_resolution
    
    # Load the image and store copy
    base_img = cv2.imread(args.input_path)
    img = base_img.copy()
    
    # Display the image and set up the mouse callback
    cv2.namedWindow(WINDOW_NAME)
    cv2.putText(img, "Press 'ESC' to reset - Press 'S' to save - Press 'Q' to quit", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    cv2.imshow(WINDOW_NAME, img)
    cv2.setMouseCallback(WINDOW_NAME, mouse_callback)
    

    
    # Main loop to listen for key presses
    while True:
        key = cv2.waitKeyEx(20)
            
        # S Key for safe
        if key == ord('s'):
            print("S key pressed")
            
            # Save the warped image if 4 points are selected
            if len(points) == 4:
                cv2.imwrite(args.output_path, img)
                print(f"Image saved as {args.output_path}")
                
            # If not, prompt the user to select 4 points before saving
            else:
                print("Please select 4 points before saving the image.")

        # ESC for exit
        if key == 27:
            print("ESC pressed")
            points.clear()
            redraw()
            
        # Q for quit
        if key == ord('q'):
            print("Q key pressed")
            break
    