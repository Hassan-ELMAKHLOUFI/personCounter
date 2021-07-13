from config.centroidtracker import CentroidTracker
from config.trackableobject import TrackableObject
from imutils.video import VideoStream
from imutils.video import FPS
from config import config
import openpyxl
#import time
import numpy as np
import argparse, imutils
import time, dlib, cv2, datetime
import sys
from itertools import zip_longest

t0 = time.time()
def run():
		#print(sys.argv[6])
		wb_obj = openpyxl.load_workbook("demo.xlsx")

		sheet_obj = wb_obj.active

		cell_obj = sheet_obj.cell(row=3, column=5)

		# construct the argument parse and parse the arguments
		ap = argparse.ArgumentParser()
		ap.add_argument("-p", "--prototxt", required=False,
			help="path to Caffe 'deploy' prototxt file")
		ap.add_argument("-m", "--model", required=True,
			help="path to Caffe pre-trained model")
		ap.add_argument("-i", "--input", type=str,
			help="path to optional input video file")
		ap.add_argument("-o", "--output", type=str,
			help="path to optional output video file")
		# confidence default 0.4
		ap.add_argument("-c", "--confidence", type=float, default=0.4,
			help="minimum probability to filter weak detections")
		ap.add_argument("-s", "--skip-frames", type=int, default=30,
			help="# of skip frames between detections")
		args = vars(ap.parse_args())

		# initialc was trained to
		# detect
		CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
			"bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
			"dog", "horse", "motorbike", "person", "pottedplant", "sheep",
			"sofa", "train", "tvmonitor"]

		# load serialized model from disk
		net = cv2.dnn.readNetFromCaffe(args["prototxt"], args["model"])

		if not args.get("input", False):
			print("[INFO] Starting the live stream..")
			vs = VideoStream(0).start()

			time.sleep(2.0)
		else:
			print("[INFO] Starting the video..")
			vs = cv2.VideoCapture(args["input"])

		writer = None
		W = None
		H = None

		# instantiate our ;pu11 tracker, then initialize a list to store
		# each of our dlib correlation trackers, followed by a dictionary to
		# map each unique object ID to a TrackableObject
		ct = CentroidTracker(maxDisappeared=40, maxDistance=50)
		trackers = []
		trackableObjects = {}

		totalFrames = 0
		totalDown = 0
		totalUp = 0
		x = []
		empty=[]
		empty1=[]

		fps = FPS().start()

		while True:
			x = x[:-1]
			frame = vs.read()
			frame = frame[1] if args.get("input", False) else frame

			if args["input"] is not None and frame is None:
				break

			frame = imutils.resize(frame, width = 500)
			rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

			if W is None or H is None:
				(H, W) = frame.shape[:2]

			if args["output"] is not None and writer is None:
				fourcc = cv2.VideoWriter_fourcc(*"MJPG")
				writer = cv2.VideoWriter(args["output"], fourcc, 30,
					(W, H), True)

			status = "Waiting"
			rects = []

			if totalFrames % args["skip_frames"] == 0:
				status = "Detecting"
				trackers = []

				blob = cv2.dnn.blobFromImage(frame, 0.007843, (W, H), 100.5)
				net.setInput(blob)
				detections = net.forward()

				for i in np.arange(0, detections.shape[2]):
					confidence = detections[0, 0, i, 2]
					if confidence > args["confidence"]:
						idx = int(detections[0, 0, i, 1])
						if CLASSES[idx] != "person":
							continue

						box = detections[0, 0, i, 3:7] * np.array([W, H, W, H])
						(startX, startY, endX, endY) = box.astype("int")

						# construct a dlib rectangle object from the bounding
						# box coordinates and then start the dlib correlation
						# tracker
						tracker = dlib.correlation_tracker()
						rect = dlib.rectangle(startX, startY, endX, endY)
						tracker.start_track(rgb, rect)

						# add the tracker to our list of trackers so we can
						# utilize it during skip frames
						trackers.append(tracker)

			else:
				for tracker in trackers:
					status = "Tracking"

					# update the tracker and grab the updated position
					tracker.update(rgb)

					pos = tracker.get_position()
					# unpack the position object
					startX = int(pos.left())
					startY = int(pos.top())
					endX = int(pos.right())
					endY = int(pos.bottom())

					# add the bounding box coordinates to the rectangles list
					rects.append((startX, startY, endX, endY))

			cv2.line(frame, (0, 120), (W, 120), (0, 0, 255), 2)
			cv2.line(frame, (0, 160), (W, 160), (0, 255, 0), 2)
			cv2.putText(frame, "SORTIE", (10, 120 -10),
				cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
			cv2.putText(frame, "ENTREE", (10, 160 -10),
				cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)

			# use the centroid tracker to associate the (1) old object
			# centroids with (2) the newly computed object centroids
			objects = ct.update(rects)

			# loop over the tracked objects
			for (objectID, centroid) in objects.items():
				# check to see if a trackable object exists for the current
				# object ID
				to = trackableObjects.get(objectID, None)

				# if there is no existing trackable object, create one
				if to is None:
					to = TrackableObject(objectID, centroid)

				# otherwise, there is a trackable object so we can utilize it
				# to determine direction
				else:
					# the difference between the y-coordinate of the *current*
					# centroid and the mean of *previous* centroids will tell
					# us in which direction the object is moving (negative for
					# 'up' and positive for 'down')
					y = [c[1] for c in to.centroids]
					direction = centroid[1] - np.mean(y)

					to.centroids.append(centroid)

					# check to see if the object has been counted or not
					if not to.counted:
						# if the direction is negative (indicating the object
						# is moving up) AND the centroid is above the center
						# line, count the object
						if direction < 0 and centroid[1] < 120:
							totalUp += 1
							empty.append(totalUp)
							to.counted = True
							#x = []
							# compute the sum of total people inside
							x.append(len(empty1)-len(empty))
							#print("Total people inside:", x)
							# if the people limit exceeds over threshold , display an alert
							if sum(x) >= config.Threshold:
								cv2.putText(frame, "ALERTE: Limite de personnes depasse", (10, frame.shape[0] - 80),
									cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 255), 2)

						# if the direction is positive (indicating the object
						# is moving down) AND the centroid is below the
						# center line, count the object
						elif direction > 0 and centroid[1] > (160):
							totalDown += 1
							empty1.append(totalDown)
							#print(empty1[-1])
							#x = []
							# compute the sum of total people inside
							x.append(len(empty1)-len(empty))
							#print("Total people inside:", x)
							# if the people limit exceeds over threshold , display an alert
							if sum(x) >= config.Threshold:
								cv2.putText(frame, "-ALERTE: Limite de personnes depasse-", (10, frame.shape[0] - 80),
									cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 255), 2)

							to.counted = True

				# store the trackable object in our dictionary
				trackableObjects[objectID] = to

				text = "ID {}".format(objectID)
				cv2.putText(frame, text, (centroid[0] - 10, centroid[1] - 10),
					cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
				cv2.circle(frame, (centroid[0], centroid[1]), 4, (255, 255, 255), -1)

			info = [
			("nombre de personnes sorties", totalUp),
			("nombre de personnes entrees", totalDown),
			]

			info2 = [
			("Total a l'interieur", totalDown-totalUp)
			]

			# Display the output
			for (i, (k, v)) in enumerate(info):
				text = "{}: {}".format(k, v)
				cv2.putText(frame, text, (10, H - ((i * 20) + 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

			for (i, (k, v)) in enumerate(info2):
				text = "{}: {}".format(k, v)
				cv2.putText(frame, text, (10, H - ((i * 20) + 60)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

			# show the output frame
			cv2.imshow("Real-Time Monitoring/Analysis Window", frame)
			key = cv2.waitKey(1) & 0xFF

			# if the `q` key was pressed, break from the loop
			if key == ord("q"):
				break

			totalFrames += 1
			fps.update()

		fps.stop()
		print("[INFO] elapsed time: {:.2f}".format(fps.elapsed()))
		print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

		if not args.get("input", False):
			vs.stop()
		else:
			vs.release()

		cv2.destroyAllWindows()

run()
