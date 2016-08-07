from __future__ import division
from ui import UI
from upload import Upload
from response import Response
import sys, os, time, traceback, threading

VERBOSE = False # Activates debug functionality if set to true

def debug(msg): # Prints out response if msg is a Response object, otherwise act like regular print
	if not VERBOSE:
		return
	if isinstance(msg, Response):
		print("Response: %s" % msg.json)
		if msg.error:
			print("Error: %s" % msg.error)
			print("Stack Trace: ")
			print(msg.stack_trace)
	else:
		print msg

def main():
	if len(sys.argv) < 2 or not sys.argv[1].lower().endswith(".pdf"):
		#ui.info("Drag a PDF on top of the application to begin converting it.")
	elif not os.path.isfile(sys.argv[1]):
		#ui.error("Incompatible File", "The file that was dragged onto the application cannot be converted. Make sure it is in PDF format.")
	if len(sys.argv) >= 2 and sys.argv[2] == "-v":
		global VERBOSE
		VERBOSE = True
		debug("Verbose mode activated")
	file_name = sys.argv[1]
	debug("Using file name: %s" % file_name)
	upload = Upload(file_name)
	# ENSURE CONNECTIVITY
	#ui.set_micro("Ensuring connectivity...", 0)
	#ui.set_macro("(1/3) Uploading PDF... ", 33)
	if not upload.online():
		#ui.error("Network Failure", "Couldn't reach http://pdf2doc.com - Perhaps the website or your Internet is down.")
	#ui.set_micro("Website online. Beginning upload...", 0)
	# UPLOAD
	def progress(monitor): # Callback for upload progress
		text = "Uploading... %s / %s bytes" % (monitor.bytes_read, monitor.len)
		percent = (monitor.bytes_read / monitor.len) * 100
		#ui.set_micro(text, percent)
	response = upload.upload(progress)
	debug("UPLOAD")
	debug(response)
	if not response.successful():
		#ui.error("Upload Failure", "Error: %s" % response.error)
	# REQUEST CONVERSION
	#ui.set_micro("Requesting conversion...", 0)
	#ui.set_macro("(2/3) Converting...", 33)
	response = upload.convert()
	debug("CONVERT")
	debug(response)
	if not response.successful():
		#ui.error("Conversion Failure", "Monitor Error: %s" % response.error)
	# MONITOR CONVERSION
	#ui.set_micro("Monitoring conversion...", 0)
	stop = False
	while not stop:
		response = upload.status()
		debug("MONITOR CONVERT")
		debug(response)
		if not response.successful():
			#ui.error("Conversion Failure", "Status Error: %s" % response.error)
		progress = response.json["progress"]
		#ui.set_micro("Monitoring conversion...", progress)
		if progress == 100:
			stop = True
			break
		time.sleep(1)
	# DOWNLOAD
	#ui.set_micro("Sending download request...", 0)
	#ui.set_macro("(3/3) Downloading DOC...", 100)
	response = upload.download()
	debug("DOWNLOAD")
	debug(response)
	request = response.request
	if not response.successful():
		#ui.error("Download Failure", "Request Error: %s"  % response.error)
	try:
		#ui.set_micro("Opening file...", 0)
		doc = open(upload.convert_result, "wb")
		#ui.set_micro("Writing to file...", 0)
		with doc:
			for chunk in request.iter_content(chunk_size = 1024):
				doc.write(chunk)
		request.close()
	except IOError as e:
		#ui.error("Download Failure", "IOError: %s" % str(e))
	except Exception as e:
		debug(traceback.format_exc())
		#ui.error("Download Failure", "Uncaught Exception: %s" % str(e))
	debug("DONE")
	#ui.quit()

def start_main():
	thread = threading.Thread(target = main)
	thread.start()

ui = UI()
ui.root.after(1000, start_main)
ui.render()
