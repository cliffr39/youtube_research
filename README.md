# youtube_research
Python app to check out potential YouTube video ideas for content creators.<br>
<br>
How to Use This Program:<br>

Install the library: Open your terminal or command prompt and run:<br>
pip install google-api-python-client<br>
<br>
Get a YouTube Data API Key:<br>
Go to the Google Cloud Console.<br>
Create a new project or select an existing one.<br>
In the navigation menu, go to "APIs & Services" > "Enabled APIs & Services". Search for "YouTube Data API v3" and enable it.<br>
Then, go to "APIs & Services" > "Credentials". Click "Create Credentials" > "API Key".<br>
Copy the generated API key.<br><br>
Insert Your API Key: In the Python code I provided, find the line API_KEY = os.environ.get('YOUTUBE_API_KEY', 'YOUR_API_GOES_HERE') and replace 'YOUR_API_GOES_HERE' with the actual API key you obtained. <br>Alternatively, you can set an environment variable named YOUTUBE_API_KEY with your key.<br>
Run the Program: Save the code as a Python file (e.g., youtube.py) <br>
and run it from your terminal: python youtube.py<br><br>
<img width="1093" alt="perp2" src="https://github.com/user-attachments/assets/46f31b86-7e10-4866-a83f-53dd8511ed1b" /><br>
<img width="1099" alt="perp1" src="https://github.com/user-attachments/assets/d28fc4bc-1e94-4151-b207-49b96c505bd3" />
