# youtube_research
Of course. Here is a cleaned-up and formatted `README.md` file suitable for GitHub, based on the information and images you provided.

-----

# YouTube Video Idea Optimizer

A desktop application built with Python and PyQt6 designed to help content creators research and optimize their video ideas. By leveraging the YouTube Data API, this tool analyzes top-ranking videos for a given topic and provides actionable insights to improve your video's title, keywords, and thumbnail.

## Features

  - **Top Title Suggestions**: See the titles of the highest-ranking videos for your topic, sorted by view count.
  - **Keyword Recommendations**: Get a list of the most frequently used and relevant tags from competing videos.
  - **Competitor Thumbnails**: View a gallery of thumbnails from top videos to inspire your own designs.
  - **Simple Interface**: Clean, two-panel layout for easy input and clear results.

## Getting Started

Follow these instructions to get the application running on your local machine.

### Prerequisites

  - Python 3.x
  - `pip` (Python package installer)

### Installation & Setup

1.  **Clone the repository (or download the source code):**

    ```bash
    git clone https://github.com/your-username/your-repository-name.git
    cd your-repository-name
    ```

2.  **Install the required Python libraries:**
    Open your terminal or command prompt and run:

    ```bash
    pip install google-api-python-client requests PyQt6
    ```

3.  **Obtain a YouTube Data API Key:**

      - Navigate to the [Google Cloud Console](https://console.cloud.google.com/).
      - Create a new project or select an existing one.
      - From the navigation menu, go to **APIs & Services** \> **Enabled APIs & Services**.
      - Click **+ ENABLE APIS AND SERVICES**, search for **YouTube Data API v3**, and enable it.
      - Go to **APIs & Services** \> **Credentials**.
      - Click **+ CREATE CREDENTIALS** and select **API Key**.
      - Copy the generated API key.

4.  **Configure the API Key:**
    In the main Python script (`gemini2_youtube.py` or your file name), locate the following line:

    ```python
    API_KEY = os.environ.get('YOUTUBE_API_KEY', 'YOUR_API_GOES_HERE')
    ```

    Replace the placeholder key with your actual API key:

    ```python
    API_KEY = os.environ.get('YOUTUBE_API_KEY', 'YOUR_API_GOES_HERE')
    ```

    *Alternatively, for better security, you can set it as a system environment variable named `YOUTUBE_API_KEY`.*

5.  **Run the Application:**
    Execute the script from your terminal:

    ```bash
    python gemini2_youtube.py
    ```

## How to Use

1.  Launch the application.
2.  On the **Ideas** screen, enter your main video topic (e.g., "Oppo Find X8 Ultra").
3.  Optionally, fill in your draft title, keywords, and script.
4.  Click the **"Get Optimization Suggestions"** button.
5.  The application will automatically switch to the **Search Results** tab to display the findings.

## Screenshots

*The simple input panel for starting your research.*

-----

<img width="1093" alt="perp2" src="https://github.com/user-attachments/assets/46f31b86-7e10-4866-a83f-53dd8511ed1b" /><br><br>
<img width="1099" alt="perp1" src="https://github.com/user-attachments/assets/d28fc4bc-1e94-4151-b207-49b96c505bd3" />
