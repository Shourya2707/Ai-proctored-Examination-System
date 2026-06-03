import cv2
import numpy as np
import base64
import os

class AIProctorEngine:
    def __init__(self):
        # Load Haar Cascades from cv2.data.haarcascades
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

    def process_frame(self, base64_img):
        """
        Process a base64 encoded image frame and return a list of active violations.
        Also returns diagnostic metrics like confidence and eye stats.
        """
        violations = []
        metrics = {
            'face_present': False,
            'face_confidence': 0.0,
            'gaze_direction': 'center',
            'objects_detected': []
        }
        
        try:
            # Decode base64 to OpenCV image
            img_data = base64.b64decode(base64_img.split(',')[1])
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return violations, metrics

            h, w, c = img.shape
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 1. Frontal Face Detection
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50)
            )

            # Heuristics for profile head-turn if frontal face is missing
            if len(faces) == 0:
                profile_faces = self.profile_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=4, minSize=(50, 50)
                )
                if len(profile_faces) > 0:
                    violations.append('HEAD_TURN')
                    metrics['face_present'] = True
                    metrics['face_confidence'] = 0.5
                else:
                    violations.append('NO_FACE')
            elif len(faces) > 1:
                violations.append('MULTIPLE_FACES')
                metrics['face_present'] = True
                metrics['face_confidence'] = 0.95
            else:
                # Single face detected - perform gaze tracking & object checks
                metrics['face_present'] = True
                metrics['face_confidence'] = 0.98
                
                (x, y, fw, fh) = faces[0]
                face_gray = gray[y:y+fh, x:x+fw]
                
                # 2. Eye & Gaze Tracking
                eyes = self.eye_cascade.detectMultiScale(
                    face_gray, scaleFactor=1.1, minNeighbors=5, minSize=(15, 15)
                )
                
                lookaway_count = 0
                for (ex, ey, ew, eh) in eyes[:2]:  # Limit to 2 eyes
                    eye_img = face_gray[ey:ey+eh, ex:ex+ew]
                    # Locate pupil (darkest point in eye)
                    _, _, min_loc, _ = cv2.minMaxLoc(eye_img)
                    pupil_x = min_loc[0]
                    
                    # Analyze if pupil is in extreme left/right margins of the eye box
                    left_margin = ew * 0.22
                    right_margin = ew * 0.78
                    
                    if pupil_x < left_margin:
                        metrics['gaze_direction'] = 'left'
                        lookaway_count += 1
                    elif pupil_x > right_margin:
                        metrics['gaze_direction'] = 'right'
                        lookaway_count += 1
                        
                if lookaway_count >= 1:
                    violations.append('EYE_LOOKAWAY')

                # 3. Secure Object Detection Heuristics
                # A: Mobile Phone Detection (High-contrast rectangle held up near face)
                blur = cv2.GaussianBlur(gray, (5, 5), 0)
                edged = cv2.Canny(blur, 50, 150)
                contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for cnt in contours:
                    # Filter small noisy contours
                    if cv2.contourArea(cnt) < 1500:
                        continue
                    
                    # Calculate bounding rect and check aspect ratio
                    rx, ry, rw, rh = cv2.boundingRect(cnt)
                    aspect_ratio = float(rw) / rh if rh > 0 else 0
                    
                    # A typical phone aspect ratio in portrait is 0.45-0.65, in landscape is 1.5-2.2
                    is_phone_aspect = (0.35 < aspect_ratio < 0.7) or (1.4 < aspect_ratio < 2.5)
                    
                    # Check proximity to face bounding box
                    near_face = (ry + rh > y) and (ry < y + fh) and (rx + rw > x - 80) and (rx < x + fw + 80)
                    
                    if is_phone_aspect and near_face:
                        # Exclude self face box mapping
                        if abs(rw - fw) > 20 and abs(rh - fh) > 20:
                            violations.append('PHONE_DETECTED')
                            metrics['objects_detected'].append('Phone')
                            break

                # B: Headphones Detection
                # Check for dark horizontal regions/ellipses crossing ears area (sides of face box)
                left_ear_region = gray[max(0, y):y+fh, max(0, x-25):x]
                right_ear_region = gray[max(0, y):y+fh, x+fw:min(w, x+fw+25)]
                
                # Check average intensities/contrast changes in ear columns
                if left_ear_region.size > 0 and right_ear_region.size > 0:
                    left_avg = np.mean(left_ear_region)
                    right_avg = np.mean(right_ear_region)
                    # Contrast differences or specific dark rings
                    if left_avg < 65 and right_avg < 65:
                        violations.append('HEADPHONES')
                        metrics['objects_detected'].append('Headphones')
            
            return violations, metrics
        except Exception as e:
            print(f"Error processing frame: {e}")
            return [], metrics
