# Website Analysis Tool

## Overview
The Website Analysis Tool is a Python-based application designed to scrape websites, analyze their content, and generate insights using AI models. It is built with a modular architecture, using Streamlit for the user interface and several custom components for scraping, data processing, and analysis.

---

## Features
- **User Authentication**: Secure login mechanism to protect access to the application.
- **File Upload**: Upload Excel files containing URLs for analysis.
- **Web Scraping**: Extract text content and metadata from websites.
- **Content Analysis**: Leverage AI models (e.g., Ollama) to analyze scraped content and extract insights.
- **Error Handling**: Graceful handling of failed scraping or analysis attempts.
- **Rate Limiting**: Control the frequency of web requests to comply with server policies.
- **Caching**: Save analysis results to reduce redundant processing.
- **Downloadable Reports**: Generate and download detailed analysis results as CSV files.

---

## Directory Structure
```
├── config
│   ├── config.py          # Configuration constants
│   ├── prompts.py         # Templates for AI analysis prompts
│   └── settings.py        # Application settings
├── input                  # Uploaded files
├── output
│   ├── analysis           # Analysis results
│   └── scraping           # Raw scraped data
├── src
│   ├── core
│   │   ├── content_analyzer.py   # AI content analysis
│   │   ├── data_processer.py     # Data processing utilities
│   │   └── scraper.py            # Web scraping logic
│   ├── utils
│   │   ├── auth.py               # Authentication logic
│   │   ├── cache.py              # Caching implementation
│   │   ├── components.py         # UI components
│   │   └── rate_limiter.py       # Rate limiting
│   └── web
│       └── app.py               # Streamlit application
```

---

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**:
   ```bash
   streamlit run src/web/app.py
   ```

---

## Usage

1. **Login**: Enter valid credentials to access the tool.
2. **Upload File**: Upload an Excel file containing URLs (one per row).
3. **Start Analysis**: Click the "Start Analysis" button to begin.
4. **View Results**: Analyze the results displayed on the dashboard.
5. **Download Results**: Download the analysis as a CSV file.

---

## Key Components

### 1. **Authentication**
Implemented in `src/utils/auth.py`. Verifies credentials to ensure secure access.

### 2. **Web Scraper**
Defined in `src/core/scraper.py`. Uses BeautifulSoup to extract text content and metadata from websites.

### 3. **Data Processor**
Implemented in `src/core/data_processer.py`. Handles cleaning and validation of URLs and manages Excel file parsing.

### 4. **Content Analyzer**
Defined in `src/core/content_analyzer.py`. Interfaces with an AI model (e.g., Ollama) to generate insights from website content.

### 5. **Rate Limiter**
Implemented in `src/utils/rate_limiter.py`. Ensures compliance with server request limits.

### 6. **Cache**
Defined in `src/utils/cache.py`. Stores previously analyzed results to optimize performance.

### 7. **UI Components**
Implemented in `src/utils/components.py`. Provides reusable Streamlit components for login and result display.

---

## Configuration

Update configuration settings in the `config/settings.py` file:
- **API Endpoints**
- **Authentication URLs**
- **Rate Limiting Thresholds**
- **Cache Directory**

---

## License

This project is licensed under the MIT License.

---

## Contributors

Feel free to contribute by submitting issues or pull requests. Ensure code quality and maintain modularity for easier integration.

---

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/).
- Web scraping powered by [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/).
- AI analysis enabled by Ollama's AI models.

