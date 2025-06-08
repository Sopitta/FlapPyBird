import cv2
import mediapipe as mp
import numpy as np

class PoseDetector:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.3,
            min_tracking_confidence=0.3,
            model_complexity=0  # Use fastest model
        )
        self.cap = cv2.VideoCapture(0)
        fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        w   = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h   = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
        self.out = cv2.VideoWriter('pose_detection.mp4',fourcc, fps, (w, h))  
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        
        self.prev_y = None
        self.jump_threshold = 0.02  
        self.is_jumping = False
        self.frame_count = 0
        self.process_every_n_frames = 1 
        
        # Set up the camera window
        #cv2.namedWindow('Pose Detection', cv2.WINDOW_NORMAL)
        #cv2.resizeWindow('Pose Detection', 640, 480)

    def detect_jump(self):
        self.frame_count += 1
        ret, frame = self.cap.read()
        if not ret:
            return False

        # Convert the BGR image to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the frame and get pose landmarks
        results = self.pose.process(rgb_frame)
        
        # Draw the pose landmarks on the frame
        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                self.mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
            )
            
            # Get the y-coordinate of the nose (landmark 0)
            current_y = results.pose_landmarks.landmark[0].y
            
            if self.prev_y is not None:
                # Calculate the change in y position
                y_change = self.prev_y - current_y
                
                # Add debug text
                cv2.putText(frame, f"Y Change: {y_change:.3f}", (50, 80), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Detect jump if there's a significant upward movement
                if y_change > self.jump_threshold and not self.is_jumping:
                    self.is_jumping = True
                    # Add jump indicator text
                    cv2.putText(frame, "JUMP!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                                1, (0, 255, 0), 2, cv2.LINE_AA)
                    return True
                elif y_change < -self.jump_threshold:
                    self.is_jumping = False
            
            self.prev_y = current_y
        
        # Show the frame
        #cv2.imshow('Pose Detection', frame)
        #cv2.waitKey(1)
        self.out.write(frame)
        
        return False

    def __del__(self):
        self.cap.release()
        self.out.release()
        cv2.destroyAllWindows()
        self.pose.close() 