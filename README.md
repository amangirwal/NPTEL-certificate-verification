# NPTEL Certificate Verification

Welcome to the **NPTEL Certificate Verification** app, hosted at [nptel-verification.streamlit.app](https://nptel-verification.streamlit.app).

This tool allows users to upload NPTEL certificates (in PDF format) for verification, extract essential information such as names and scores, and compare the data with online verification links or QR codes. It supports both bulk verification of multiple certificates and single certificate verification.

## Features

- **Bulk Certificate Verification**: Upload multiple NPTEL certificates in PDF format and verify them in one go.
- **Single Certificate Verification**: Upload a single certificate and extract relevant information like name, scores, and verification status.
- **Extract QR Codes**: Scans the PDF for embedded QR codes and verifies the certificate by fetching the final verification link.
- **Extract Certificate Information**: Extracts names, marks, assignment, and proctored exam scores directly from the PDF.
- **Verification Link Extraction**: Identifies and fetches certificate URLs embedded within the PDF for further verification.

## Project Structure

- **`pyt.py`**: Contains the main logic for processing and extracting data from the PDF files.
- **`requirements.txt`**: Lists the necessary Python packages for the project.
- **`streamlit_app.py`**: Streamlit interface for the project.
  
## Technologies Used

- **Python**: Core logic for PDF processing and text extraction.
- **Streamlit**: For building the user interface.
- **PyMuPDF (Fitz)**: To extract text and images from PDFs.
- **Pillow (PIL)**: To handle image data and QR code extraction.
- **Pyzbar**: For scanning and decoding QR codes from PDFs.
- **BeautifulSoup**: To scrape certificate verification URLs when QR codes are unavailable.
- **Pandas**: For handling data and creating structured outputs like Excel sheets.

## Installation Instructions

To run this project locally, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/nptel-verification.git
   cd nptel-verification
