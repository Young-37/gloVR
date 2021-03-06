import cv2
import numpy as np
import time
import math
import socket


#TODO
#onOff = 파이썬 받은 문자열


UDP_IP = "127.0.0.1"
UDP_PORT = 5065


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Open Camera object
cap = cv2.VideoCapture(0)

# Decrease frame size
cap.set(3, 500)
cap.set(4, 450)

def nothing():
    pass


# Function to find angle between two vectors
def Angle(v1, v2):
    dot = np.dot(v1, v2)
    x_modulus = np.sqrt((v1 * v1).sum())
    y_modulus = np.sqrt((v2 * v2).sum())
    cos_angle = dot / x_modulus / y_modulus
    angle = np.degrees(np.arccos(cos_angle))
    return angle


# Function to find distance between two points in a list of lists
def FindDistance(A, B):
    return np.sqrt(np.power((A[0][0] - B[0][0]), 2) + np.power((A[0][1] - B[0][1]), 2))


# Creating a window for HSV track bars
cv2.namedWindow('HSV_TrackBar')

# Starting with 100's to prevent error while masking
h, s, v = 100, 100, 100

# Creating track bar
cv2.createTrackbar('h', 'HSV_TrackBar', 0, 179, nothing)
cv2.createTrackbar('s', 'HSV_TrackBar', 0, 255, nothing)
cv2.createTrackbar('v', 'HSV_TrackBar', 0, 255, nothing)

cxcyCount = 0

print("통신성공! ")
while (1):
    # Measure execution time
    start_time = time.time()

    # Capture frames from the camera
    ret, frame = cap.read()

    # Blur the image
    blur = cv2.blur(frame, (3, 3))

    # Convert to HSV color space
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)

    # Create a binary image with where white will be skin colors and rest is black
    mask2 = cv2.inRange(hsv, np.array([45,65,65]), np.array([75,255, 255]))
    #mask2 = cv2.inRange(hsv, np.array([2, 50, 50]), np.array([15, 255, 255]))

    # Kernel matrices for morphological transformation
    kernel_square = np.ones((11, 11), np.uint8)
    kernel_ellipse = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

    # Perform morphological transformations to filter out the background noise
    # Dilation increase skin color area
    # Erosion increase skin color area
    dilation = cv2.dilate(mask2, kernel_ellipse, iterations=1)
    erosion = cv2.erode(dilation, kernel_square, iterations=1)
    dilation2 = cv2.dilate(erosion, kernel_ellipse, iterations=1)
    filtered = cv2.medianBlur(dilation2, 5)
    kernel_ellipse = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))
    dilation2 = cv2.dilate(filtered, kernel_ellipse, iterations=1)
    kernel_ellipse = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    dilation3 = cv2.dilate(filtered, kernel_ellipse, iterations=1)
    median = cv2.medianBlur(dilation, 5)
    ret, thresh = cv2.threshold(median, 127, 255, 0)

    # Find contours of the filtered frame

    contours, hierarchy = cv2.findContours(median, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)


    # Draw Contours
    # cv2.drawContours(frame, cnt, -1, (122,122,0), 3)
    # cv2.imshow('Dilation',median)

    # Find Max contour area (Assume that hand is in the frame)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask2 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, kernel, 1)

    max_area = 100
    ci = 0
    for i in range(len(contours)):
        cnt = contours[i]
        area = cv2.contourArea(cnt)
        if (area > max_area):
            max_area = area
            ci = i

        # Largest area contour

    if not contours :
        ret, frame = cap.read()
        cv2.imshow("mask2",mask2)
        cv2.imshow("1",frame)
        ###############################
        # Print execution time
        # print time.time()-start_time

        # close the output video by pressing 'ESC'
        k = cv2.waitKey(5) & 0xFF
        if k == 27:
            break

        continue

    cnts = contours[ci]

    # Find convex hull
    hull = cv2.convexHull(cnts)

    # Find convex defects
    hull2 = cv2.convexHull(cnts, returnPoints=False)
    defects = cv2.convexityDefects(cnts, hull2)

    # Get defect points and draw them in the original image
    FarDefect = []
    if defects is None:
        nothing()
    else:
        for i in range(defects.shape[0]):
            s, e, f, d = defects[i, 0]
            start = tuple(cnts[s][0])
            end = tuple(cnts[e][0])
            far = tuple(cnts[f][0])
            FarDefect.append(far)
            #cv2.line(frame, start, end, [0, 255, 0], 1)
            #cv2.circle(frame, far, 10, [100, 255, 255], 3)

    # Find moments of the largest contour
    moments = cv2.moments(cnts)

    # Central mass of first order moments 이 값 보내주면 될듯!!!!!
    #filteredvalue = filteredvalue * (1 - alpha) + flexvalue * alpha;

    # TODO = LPF for cx,cy

    """
    1.cx2,cy2에 이전의 cx, cy 저장 (맨 처음에는 같은 값 저장)
    2.cx,cy에 새로 들어오는 값 저장
    """

    if moments['m00'] != 0:
        # 맨 처음에는 이전의 값을 같은 값으로 넣어주기
        if cxcyCount == 0 :

            cx = int(moments['m10'] / moments['m00'])  # cx = M10/M00
            cy = int(moments['m01'] / moments['m00'])  # cy = M01/M00

            cx2 = cx
            cy2 = cy

            print("cx = ",cx2)
            print("cy = ",cy2)
            cxcyCount = cxcyCount+1
        # 두 번째 부터 이전 값 저장하고 새로들어오는값이랑 계산해서 필터
        else :
            cx2 = cx
            cy2 = cy
            cx = int(moments['m10'] / moments['m00'])  # cx = M10/M00
            cy = int(moments['m01'] / moments['m00'])  # cy = M01/M00
            cx2 = int(cx2 * (0.5) + cx * 0.5)
            cy2 = int(cy2 * (0.5) + cy * 0.5)
            print("cx = ", cx2)
            print("cy = ", cy2)

    centerMass = (cx2, cy2)

    # Draw center mass

    cv2.circle(frame, centerMass, 7, [100, 0, 255], 2)
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(frame, 'Center', tuple(centerMass), font, 2, (255, 255, 255), 2)

    # Distance from each finger defect(finger webbing) to the center mass
    distanceBetweenDefectsToCenter = []
    for i in range(0, len(FarDefect)):
        x = np.array(FarDefect[i])
        centerMass = np.array(centerMass)
        distance = np.sqrt(np.power(x[0] - centerMass[0], 2) + np.power(x[1] - centerMass[1], 2))
        distanceBetweenDefectsToCenter.append(distance)

    # Get an average of three shortest distances from finger webbing to center mass
    sortedDefectsDistances = sorted(distanceBetweenDefectsToCenter)
    AverageDefectDistance = np.mean(sortedDefectsDistances[0:2])

    # Get fingertip points from contour hull
    # If points are in proximity of 80 pixels, consider as a single point in the group
    finger = []
    for i in range(0, len(hull) - 1):
        if (np.absolute(hull[i][0][0] - hull[i + 1][0][0]) > 80) or (
                np.absolute(hull[i][0][1] - hull[i + 1][0][1]) > 80):
            if hull[i][0][1] < 500:
                finger.append(hull[i][0])

    # The fingertip points are 5 hull points with largest y coordinates
    finger = sorted(finger, key=lambda x: x[1])
    fingers = finger[0:5]

    # Calculate distance of each finger tip to the center mass
    fingerDistance = []
    for i in range(0, len(fingers)):
        distance = np.sqrt(np.power(fingers[i][0] - centerMass[0], 2) + np.power(fingers[i][1] - centerMass[0], 2))
        fingerDistance.append(distance)

    # Finger is pointed/raised if the distance of between fingertip to the center mass is larger
    # than the distance of average finger webbing to center mass by 130 pixels
    result = 0
    for i in range(0, len(fingers)):
        if fingerDistance[i] > AverageDefectDistance + 130:
            result = result + 1

    ##### Show final image ########
    cv2.imshow("mask2", mask2)
    cv2.imshow("1",frame)
    ###############################

    # Print execution time
    # print time.time()-start_time

    # close the output video by pressing 'ESC'
    k = cv2.waitKey(5) & 0xFF
    if k == 27:
        break

    try:

        sock.sendto((str(cx2)+","+str(cy2)).encode(), (UDP_IP, UDP_PORT) )
        print((str(cx2)+","+str(cy2)))
    except:
        pass

    # try:
    #     UDP_DATA,addr = sock.recvfrom(3)
    #     print("receive data : ",UDP_DATA)
    #     print("receive port : ",addr[0],addr[1])
    # except:
    #     pass

cap.release()
cv2.destroyAllWindows()
