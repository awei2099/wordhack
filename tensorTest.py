import cv2
import numpy as np
from statistics import median
from PIL import Image
import tensorflow.lite as tflite
from picamera2 import Picamera2

# Function to preprocess the image for TFLite model
def preprocess_image(image):
    img = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)  # Convert grayscale to RGB
    img = cv2.resize(img, (224, 224))  # Resize to model input size
    img_array = np.array(img) / 255.0  # Normalize pixel values to [0, 1]
    img_array = np.expand_dims(img_array, axis=0).astype(np.float32)  # Add batch dimension
    return img_array
    
def preprocess_image2(image):
    img = Image.open(image).convert('RGB')  # Convert grayscale to RGB
    img = img.resize((224, 224))  # Resize to model input size
    img_array = np.array(img) / 255.0  # Normalize pixel values to [0, 1]
    img_array = np.expand_dims(img_array, axis=0).astype(np.float32)  # Add batch dimension
    return img_array

# Load the TFLite model
interpreter = tflite.Interpreter(model_path="model.tflite")
interpreter.allocate_tensors()

# Get input and output details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Class mapping
class_indices = {
    'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 
    'G': 6, 'H': 7, 'I': 8, 'K': 9, 'L': 10, 
    'M': 11, 'N': 12, 'O': 13, 'P': 14, 'Q': 15, 'R': 16, 
    'S': 17, 'T': 18, 'U': 19, 'V': 20, 'W': 21, 'X': 22, 
    'Y': 23
}  # Replace with your actual class mapping
labels = {v: k for k, v in class_indices.items()}

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

picam2.stop()

# Convert to YCrCb color space
ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)

# Define the lower and upper bounds for the color mask
#lower_scalar = np.array([85.0, 55.9, 110.3])
#upper_scalar = np.array([255.0, 255.0, 255.0])

lower_scalar = np.array([100.9, 35.0, 100.6])
upper_scalar = np.array([233.8, 249.3, 192.7])


# Apply mask
thresh = cv2.inRange(ycrcb, lower_scalar, upper_scalar)


# Find contours
img = image.copy()
contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

cv2.imwrite('testImages\img2.png', thresh)

filt_cont = []
for contour in contours:
    x, y, w, h = cv2.boundingRect(contour)
    area = cv2.contourArea(contour)
    perim = cv2.arcLength(contour, True)

    if perim == 0:  # Avoid division by zero
        continue

    circ = (4 * np.pi * area) / (perim ** 2)
    aspect_ratio = w / float(h)

    # Filter for square-like contours
    if 0.90 <= aspect_ratio <= 1.1 and w > 55 and circ < 0.9:
        filt_cont.append(contour)

cv2.drawContours(img, filt_cont, -1, (255, 0, 0), 7)
cv2.imwrite("img3.png", img)

filt_cont.reverse()
print(len(filt_cont))

final_string = ""
box_index = 1

for minibox in filt_cont:
    x, y, w, h = cv2.boundingRect(minibox)
    print(x, y, w, h)

    avg_side = (w + h) / 2
    modif = int(avg_side * 0.05)
    crop_img = image[(y + modif):(y + h - modif), (x + modif):(x + w - modif)]
    path = 'letterIGs\letter' + str(box_index) + '.png'
    cv2.imwrite(path, crop_img)
    
    # Preprocess the cropped image for the model
    processed_img = preprocess_image2(path)

    # Run inference
    interpreter.set_tensor(input_details[0]['index'], processed_img)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])

    # Get predicted class
    predicted_class = np.argmax(output_data[0])
    predicted_label = labels[predicted_class]
    print(f"Predicted Label: {predicted_label}, Confidence: {output_data[0][predicted_class]}")
    
    cv2.imshow("ewrwer", crop_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    # Append to final string
    final_string += predicted_label

    # Save cropped image for debugging
    box_index += 1

print("Final String:", final_string)
