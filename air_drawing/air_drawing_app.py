import cv2
import numpy as np
import math

cap = cv2.VideoCapture(0)

lower_color = np.array([100, 150, 50])
upper_color = np.array([140, 255, 255])

points = []  # (x, y, z)
current_z = 0
angle = 0

screen_h, screen_w = 600, 1000

cv2.namedWindow("3D Drawing", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("3D Drawing", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

canvas = np.ones((screen_h, screen_w, 3), dtype=np.uint8) * 255


def rotate(x, y, z, angle):
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    x_new = x * cos_a - z * sin_a
    z_new = x * sin_a + z * cos_a
    return x_new, y, z_new


def project(x, y, z):
    f = 300
    z += 400
    px = int((x * f) / z + screen_w // 2)
    py = int((y * f) / z + screen_h // 2)
    return px, py


while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, (screen_w, screen_h))

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_color, upper_color)
    mask = cv2.GaussianBlur(mask, (5, 5), 0)

    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        c = max(contours, key=cv2.contourArea)

        if cv2.contourArea(c) > 500:
            x, y, w, h = cv2.boundingRect(c)
            cx = x + w // 2 - screen_w // 2
            cy = y + h // 2 - screen_h // 2

            points.append((cx, cy, current_z))

            # limit points (important)
            if len(points) > 300:
                points.pop(0)

    canvas[:] = 255

    # Draw all layers
    for i in range(1, len(points)):
        x1, y1, z1 = rotate(*points[i-1], angle)
        x2, y2, z2 = rotate(*points[i], angle)

        p1 = project(x1, y1, z1)
        p2 = project(x2, y2, z2)

        # Create glow layer
        glow_layer = np.zeros_like(canvas)

        for i in range(1, len(points)):
            x1, y1, z1 = rotate(*points[i-1], angle)
            x2, y2, z2 = rotate(*points[i], angle)

            p1 = project(x1, y1, z1)
            p2 = project(x2, y2, z2)

            # 🎨 Neon color (cyan style)
            color = (
                (i * 5) % 256,
                (i * 3) % 256,
                (i * 7) % 256
            )

            # Draw thick line for glow
            cv2.line(glow_layer, p1, p2, color, 6)

        # Blur for glow effect
        glow_layer = cv2.GaussianBlur(glow_layer, (11, 11), 0)

        # Combine glow with canvas
        canvas = cv2.addWeighted(canvas, 1, glow_layer, 0.6, 0)

        # Draw sharp core line
        for i in range(1, len(points)):
            x1, y1, z1 = rotate(*points[i-1], angle)
            x2, y2, z2 = rotate(*points[i], angle)

            p1 = project(x1, y1, z1)
            p2 = project(x2, y2, z2)

            cv2.line(canvas, p1, p2, (0, 0, 0), 2)

    # Camera preview
    preview = cv2.resize(frame, (200, 150))
    canvas[10:160, screen_w-210:screen_w-10] = preview

    cv2.putText(canvas, "Z/X: Depth | A/D: Rotate | Q: Exit | C: Clear", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2)

    cv2.imshow("3D Drawing", canvas)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break
    elif key == ord('c'):
        points = []
    elif key == ord('z'):
        current_z += 50
    elif key == ord('x'):
        current_z -= 50
    elif key == ord('a'):
        angle -= 0.1
    elif key == ord('d'):
        angle += 0.1

cap.release()
cv2.destroyAllWindows()