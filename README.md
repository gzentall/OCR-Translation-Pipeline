# OCR Translation Pipeline

This project provides a complete pipeline for processing PDF documents with handwriting recognition and translation. It uses **Google Vision API** for OCR and **Google Translate API** for translation, with both a command-line interface and a modern web frontend.

## Features

- 📄 **PDF OCR**: Convert handwritten PDFs to text using Google Vision API
- 🌍 **Translation**: Translate recognized text to English using Google Translate API  
- 🖥️ **Web Interface**: Modern, responsive web application for easy document processing
- 📱 **Drag & Drop**: Simple file upload with drag-and-drop support (up to 200MB)
- 📊 **Real-time Status**: Live system status monitoring
- 💾 **Download Results**: Download translated text files

## Directory structure

- `letters/inbox/` – Place your input PDF documents here.  Each PDF should contain one or more scanned pages.
- `letters/work/` – Intermediate files generated during OCR (temporary images and combined text output).
- `letters/out/` – Final outputs, organised into subfolders:
  - `pdf/` – OCR‑enhanced PDFs (coming in future steps).
  - `en/` – English translations (use the translation scripts from the previous starter kit or the Argos/DeepL scripts).
  - `qa/` – HTML QA pages (optional, see the other kit).
- `scripts/` – Helper scripts.  The most important one here is `run_vision_ocr.sh`, which calls Google’s Vision API for each page of a PDF.
- `.gcp_api_key` – **You must create this file yourself.**  Put your Google Cloud Vision API key on a single line in this file.  See below for details.
- `mcp/servers.json` – A sample MCP server definition that exposes the Vision OCR script to Cursor’s Model Context Protocol.  You can import this JSON into Cursor to run OCR from within the IDE.

## Quick Start

### Option 1: Web Interface (Recommended)

1. **Run the setup script**:
   ```bash
   python3 setup.py
   ```

2. **Start the web application**:
   ```bash
   python3 app.py
   ```

3. **Open your browser** and go to `http://localhost:5000`

4. **Upload a PDF** using the drag-and-drop interface

### Option 2: Command Line Interface

```bash
# Process a single PDF
bash scripts/run_vision_ocr.sh letters/inbox/your_document.pdf

# Translate the OCR result
python3 scripts/translate_google.py letters/work/your_document.vision.txt

# Process all PDFs in inbox
bash scripts/run_all_vision_ocr.sh
```

## Prerequisites

To use this project you will need the following:

1. **Python 3.7+** – Make sure Python 3.7 or higher is installed

2. **Google Cloud account** – If you don't already have one, go to [console.cloud.google.com](https://console.cloud.google.com/) and sign up.

3. **Create a Google Cloud project** – In the console, click the project dropdown and choose **New project**.  Give it a name (e.g. "OCR Translation") and click **Create**.

4. **Enable APIs** – Select your project, then enable both:
   - **Vision API** (for OCR)
   - **Translation API** (for translation)

5. **Create an API key** – In **APIs & Services → Credentials**, click **Create credentials → API key**.  Copy the key string.

6. **Populate `.gcp_api_key`** – In this repository's root, create a file named `.gcp_api_key` and paste your API key into it.

7. **Install Docker** – The OCR script relies on a small container (`ghcr.io/johnleetw/poppler:latest`) to convert PDFs to images.  Make sure Docker is installed and running on your system.

## Running OCR

Once the prerequisites are satisfied, drop a PDF file (e.g. `my_letter.pdf`) into `letters/inbox/`.  Then run the following from the project root:

```bash
bash scripts/run_vision_ocr.sh letters/inbox/my_letter.pdf
```

This will:

1. Convert the PDF into high‑resolution PNG images using Poppler.
2. Send each page to the Google Vision API for **DOCUMENT_TEXT_DETECTION**.
3. Concatenate the extracted text into `letters/work/<filename>.vision.txt`.

If the PDF contains printed text, this method will work fine.  If it contains cursive handwriting, results will depend on the handwriting’s legibility.  Because the Vision API uses machine learning models trained on a variety of handwriting samples, it generally outperforms Tesseract on cursive documents.

## Integrating with Cursor

The included `mcp/servers.json` exposes a simple **vision_ocr** server that calls `scripts/run_vision_ocr.sh`.  To use it in Cursor:

1. Copy the contents of `mcp/servers.json` into your global MCP configuration or add it via **Cursor Settings → MCP → Add New Global MCP Server**.
2. In your project, you can then call `vision_ocr` on a PDF, and the script will return the path to the generated text file.

## Web Interface

The web interface provides a modern, user-friendly way to process documents:

### Features
- **Drag & Drop Upload**: Simply drag PDF files onto the upload area
- **Real-time Progress**: See processing status with progress bars
- **System Status**: Monitor API keys, Docker, and script availability
- **Download Results**: Download translated text files directly
- **Error Handling**: Clear error messages and troubleshooting info

### Starting the Web Server
```bash
python3 app.py
```

The server will start on `http://localhost:5000` by default.

## Translation

The project includes a Google Translate integration script (`scripts/translate_google.py`) that automatically translates OCR results to English. The web interface handles this automatically, but you can also use it from the command line:

```bash
python3 scripts/translate_google.py letters/work/document.vision.txt
```

### Translation Options
- **Auto-detect language**: Automatically detects the source language
- **Custom target language**: Specify different target languages (default: English)
- **Batch processing**: Process multiple files at once

## Costs and quota

The Vision API has a generous free tier, but you should monitor usage.  Each page sent to `DOCUMENT_TEXT_DETECTION` counts as one unit.  If you process many pages, charges may apply.  See the [Vision API pricing page](https://cloud.google.com/vision/pricing) for details.

## Troubleshooting

- **Missing or invalid API key:** Ensure your `.gcp_api_key` file exists and contains only the key string.  The script will exit with an error if it cannot read the key.
- **Poppler container download fails:** Confirm that Docker is installed and you have internet access.  The script pulls the container image if it isn’t already present.
- **API errors:** The Vision API may return errors for very large images or malformed requests.  Check the console output for clues.  You can also pass `--debug` to `curl` in the script if you need to inspect responses.