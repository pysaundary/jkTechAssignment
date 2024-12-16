# jkTechAssignment
 
This README provides instructions on how to set up and run the project.

for completing this assignment, i follow this tutorial and also take help form CHAT GPT , Stackoverflow posts
https://medium.com/@jiangan0808/retrieval-augmented-generation-rag-with-open-source-hugging-face-llms-using-langchain-bd618371be9d

Prerequisites:

Python 3.12 (or later): Download and install Python from https://www.python.org/downloads/ if you don't have it already.
pip: This package manager comes bundled with Python versions 3.4 and later. You can verify its installation by running pip --version in your terminal. If not installed, refer to the official documentation for instructions: https://pip.pypa.io/en/stable/installation/
Installation:

Download the Project:

You can download the project as a ZIP archive from [source link here (replace with your download link)].
Alternatively, you can clone the project using Git if available:
Bash

git clone https://https://git-scm.com/@[username]/[project_name].git
Extract the Project:

If you downloaded a ZIP archive, extract the contents to your desired location.
Install Dependencies:

Open a terminal or command prompt and navigate to the extracted project directory.
Create a python3.12 venv with venv name using : python -m venv venv

Run the following command to install the required Python packages listed in requirements.txt:
Bash

pip install -r requirements.txt
Configure the Project (Optional):

The project might use configuration files located in the config directory. Edit these files according to your needs. Refer to the specific configuration options within these files for further instructions.
Run the Project:

From the project directory, execute the following command to start the application:
Bash

python main.py
Additional Notes:

Configuration Files: If the project doesn't require configuration file edits, step 4 can be skipped.
Background Process: If your application runs continuously (like a web server), this execution method might be suitable. If your main.py performs a specific task and exits, consider wrapping it in a loop or using a process manager like supervisord within the container for continuous execution.
Troubleshooting: If you encounter any issues during installation or execution, refer to the project's documentation (if available) or consult online resources for troubleshooting Python applications.
This README provides a basic guide to get you started with the project. Feel free to explore the project's code and documentation for further details and customization options.

Directory Structure

Root Folder:

config folder: Contains configuration files (e.g., config.json).
logs folder: Used to store application logs.
media folder: Used to store PDF files.
other folder (Optional): Currently contains miscellaneous files like scripts (e.g., .bat and .sh files) related to log removal.
src folder: Contains all the source code organized into subdirectories.
main.py: The main script that serves as the starting point for the application.


APIS

Swagger link 
http://localhost:8003/docs#/


for upload document : curl -X 'POST' \
  'http://localhost:8003/llm-api/upload_files/?user_id=psaundary&topic=geeta' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'files=@bhagavad-gita-in-english-source-file.pdf;type=application/pdf'

for getting list of documents : curl -X 'GET' \
  'http://localhost:8003/llm-api/get_user_files/?user_id=psaundary&limit=10&order_by=true&offset=0&topicName=geeta' \
  -H 'accept: application/json'

for ask question : curl -X 'POST' \
  'http://localhost:8003/llm-api/ask-question/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "question": "chapter 1 summary",
  "topicUUID": "6ba3e499-9df7-4917-889d-6d3d73ec9bd6"
}'

for enable disable document : curl -X 'GET' \
  'http://localhost:8003/llm-api/enable-and-disable-topic/?topic_uuid=6ba3e499-9df7-4917-889d-6d3d73ec9bd6&isActive=false' \
  -H 'accept: application/json'