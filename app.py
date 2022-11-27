# -*- coding: utf-8 -*-
"""
Created on Sun Nov 20 13:11:33 2022

@author: Lidia
"""

from flask import Flask
import os
import urllib.request
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import json
import base64
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential

# ml_client = MLClient(
# DefaultAzureCredential(), subscription_id, resource_group, workspace
# )

UPLOAD_FOLDER = 'static/uploads/'

app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

#workspace definition

credential = DefaultAzureCredential()
ml_client = None
try:
    ml_client = MLClient.from_config(credential)
except Exception as ex:
    print(ex)
    # Enter details of your AML workspace
    subscription_id = "fcd507c3-2157-4d7e-8f34-7f992556b828"
    resource_group = "tumor_detection_project"
    workspace = "tumor_detection"
    ml_client = MLClient(credential, subscription_id, resource_group, workspace)


ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
	
@app.route('/')
def upload_form():
	return render_template('upload.html')

@app.route('/', methods=['POST'])
def upload_image():
	if 'file' not in request.files:
		flash('No file part')
		return redirect(request.url)
	file = request.files['file']
	if file.filename == '':
		flash('No image selected for uploading')
		return redirect(request.url)
	if file and allowed_file(file.filename):
		filename = secure_filename(file.filename)
		file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

		with open(app.config['UPLOAD_FOLDER'] + filename, mode='rb') as myfile:
			img = myfile.read()

		request_json = {
			"input_data": {
				"columns": ["image"],
				"data": [base64.encodebytes(img).decode("utf-8")],
			}
		}

		request_file_name = "sample_request_data.json"

		with open(request_file_name, "w") as request_file:
			json.dump(request_json, request_file)

		resp = ml_client.online_endpoints.invoke(
			endpoint_name='tumor-endpoint-test11271017',
			deployment_name="brain-mri-image-final",
			request_file=request_file_name,
		)
		print(resp)

		#print('upload_image filename: ' + filename)
		#flash('Image successfully uploaded and displayed below')
		return render_template('upload.html', filename=filename)
	else:
		flash('Allowed image types are -> png, jpg, jpeg, gif')
		return redirect(request.url)

@app.route('/display/<filename>')
def display_image(filename):
	#print('display_image filename: ' + filename)
	return redirect(url_for('static', filename='uploads/' + filename), code=301)

if __name__ == "__main__":
    app.run()