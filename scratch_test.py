import sys
import mediapipe as mp

print("Dir mp:", dir(mp))

try:
    import mediapipe.python.solutions.face_mesh as mp_face_mesh
    print("Imported mediapipe.python.solutions.face_mesh successfully!")
except Exception as e:
    print("Error importing face_mesh directly:", e)
