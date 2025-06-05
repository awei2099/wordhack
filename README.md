# WordHack

WordHack is a Raspberry Pi–powered system that captures a WordHunt (or Boggle‐style) grid, recognizes each letter, solves the puzzle, and then uses a microcontroller (e.g., on a CNC or 3D‐printer–style motion system) to trace out all valid words in sequence. It integrates:

- **Computer Vision & OCR** (via OpenCV and either Tesseract or a TensorFlow Lite model) to detect letters in a live camera frame.  
- **Java‐based Solver** (`wordhunthack.jar`) that takes a 16‐letter string as input and outputs G‐code commands to draw each found word.  
- **Serial Control** of a microcontroller (e.g., running Marlin or custom G‐code firmware) over USB to physically trace each word.  
- **LCD + Button Interface** to display recognized letters, let you correct uncertain characters, and choose whether to use Tesseract OCR (fast, but less accurate) or a custom TensorFlow Lite model (more accurate) for letter recognition.

