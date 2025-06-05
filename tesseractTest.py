import cv2
import pytesseract
import numpy as np
from statistics import median
import imutils
from picamera2 import Picamera2

picam2 = Picamera2()

picam2.start()
image = None

while True:
    frame = picam2.capture_array()
    cv2.imshow("preview", frame)
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('\r'):
        image = frame
        break
    elif key == ord('q'):
        break

cv2.imwrite("img1.png",image)
cv2.destroyAllWindows()
picam2.stop()

# Convert to YCrCb color space
ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)

# Define the lower and upper bounds for the color mask
lower_scalar = np.array([94.9, 0.0, 100.6])
upper_scalar = np.array([233.8, 249.3, 192.7])

# mask
# mask = cv2.inRange(ycrcb, lower_scalar, upper_scalar)
thresh = cv2.inRange(ycrcb, lower_scalar, upper_scalar)

# mask display
display_scale = 1
output_height, output_width = thresh.shape[:2]
print(output_width)
new_width = int(output_width * display_scale)
new_height = int(output_height * display_scale)
small_mask = cv2.resize(thresh, (new_width, new_height), interpolation=cv2.INTER_AREA)

cv2.imshow('Color Mask', small_mask)
cv2.waitKey(0)
cv2.destroyAllWindows()

# --------------------------------------------------------------------------

img = image.copy()
# contours, _ = cv2.findContours(...) # Your call to find the contours using OpenCV 2.4.x
contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) # Your call to find the contours

filt_cont = []

for contour in contours:
    x, y, w, h = cv2.boundingRect(contour)
    # Calculate the aspect ratio
    area = cv2.contourArea(contour)
    perim = cv2.arcLength(contour, True)


    if perim == 0:  # Avoid division by zero
            continue
    
    circ = (4 * np.pi * area) / (perim ** 2)
    aspect_ratio = w / float(h)
    # Filter for square-like contours based on aspect ratio and size
    if 0.90<= aspect_ratio <= 1.1 and w > 65 and circ < 9.0:
        filt_cont.append(contour)

cv2.drawContours(img, filt_cont, -1, (255,0,0), 7)

small_cont = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)

cv2.imshow("contour_img", small_cont)
cv2.waitKey(0)

filt_cont.reverse()
print(len(filt_cont))

final_string = ""
box_index = 1

data = []

for minibox in filt_cont:
    x,y,w,h = cv2.boundingRect(minibox)
    print(x, y, w, h)
    avg_side = (w + h)/2
    modif = int(avg_side * .1)
    crop_img = thresh[(y+modif):(y+h-modif), (x+modif):(x+w-modif)]
    cv2.imshow("crop_img", crop_img)
    letter_detect = pytesseract.image_to_string(crop_img, config='--psm 10 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    
    if len(letter_detect) == 0:
        letter_detect ='Z'
    else:
        letter_detect = letter_detect[0]
        if letter_detect == '|':
            letter_detect = 'I'
        elif letter_detect == '0':
            letter_detect = 'O'
    cv2.imwrite("letterIMGs/letter" + str(box_index) +".jpg", crop_img)
    cv2.waitKey(0)
    box_index += 1 
    data.append([letter_detect, x, y]) 
    
data.sort(key=lambda x: x[2])

sorted_data = []
for i in range(0, 16, 4):
    group = data[i:i +4]
    group.sort(key=lambda x:x[1])
    sorted_data.extend(group)

for thr in sorted_data:
    final_string = final_string + thr[0]
    
print(final_string)
