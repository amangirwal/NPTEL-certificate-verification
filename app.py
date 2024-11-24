import streamlit as st
import fitz  
from PIL import Image
from pyzbar.pyzbar import decode
import io
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

def extract_text_from_pdf(pdf_bytes):
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text += page.get_text()
    return text

def extract_qr_codes_from_pdf(pdf_bytes):
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    qr_codes = []
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes()))
        qr_codes_page = decode(img)
        for qr in qr_codes_page:
            qr_codes.append(qr.data.decode('utf-8'))
    return qr_codes

def extract_name_and_scores(text):  
    lines = text.split('\n')
    name = None
    assignment_score = None
    proctored_score = None
    marks = None

    uppercase_pattern = re.compile(r'\b[A-Z][A-Z\s]+\b')
    for i, line in enumerate(lines):
        line = line.strip()
        
        if uppercase_pattern.match(line) and not re.search(r'\d+', line):
            name = line
            assignment_score = lines[i + 1].strip().split('/')[0].strip()  # Next line after name
            proctored_score = lines[i + 2].strip().split('/')[0].strip()  # Line after assignment score
            marks = lines[i + 3].strip()  # Line after proctored score
            break

    return name, marks, assignment_score, proctored_score

def extract_pdf_link_from_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        link = soup.find('a', string='Course Certificate')
        if link and link.get('href'):
            pdf_url = link['href']
            if not pdf_url.startswith('http'):
                pdf_url = requests.compat.urljoin(url, pdf_url)
            return pdf_url
        else:
            st.error(f"No 'Course Certificate' link found at {url}")
    except requests.RequestException as e:
        st.error(f"Error accessing URL {url}: {e}")
    return None

def download_pdf(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return io.BytesIO(response.content)
    except requests.RequestException as e:
        st.error(f"Error downloading PDF from {url}: {e}")
        return None

def extract_link(pdf_bytes):
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    found_url = None
    url_prefix = "https://internalapp.nptel.ac.in/"
    for page_number in range(len(document)):
        page = document.load_page(page_number)
        links = page.get_links()
        
        for link in links:
            uri = link.get("uri", None)
            if uri and uri.startswith(url_prefix):
                found_url = uri
                break  # Exit the loop once the first matching URL is found
    
        if found_url:
            return found_url
    
    return None

def process_pdf(pdf_bytes):
    text = extract_text_from_pdf(pdf_bytes)
    qr_codes = extract_qr_codes_from_pdf(pdf_bytes)
    original_name, original_marks, assignment_score, proctored_score = extract_name_and_scores(text)
    
    # Check if there are QR codes or if we need to use the extracted link
    if qr_codes:
        verification_results = []
        for qr in qr_codes:
            unique_id = qr.split('/')[-1]
            final_url = f"https://archive.nptel.ac.in/noc/Ecertificate/?q={unique_id}"
            extracted_pdf_link = extract_pdf_link_from_page(final_url)
            if extracted_pdf_link:
                fetched_pdf = download_pdf(extracted_pdf_link)
                if fetched_pdf:
                    fetched_pdf_text = extract_text_from_pdf(fetched_pdf)
                    fetched_name, fetched_marks, _, _ = extract_name_and_scores(fetched_pdf_text)
                    status = 'Verified' if (original_name == fetched_name and original_marks == fetched_marks) else 'Not Verified'
                    verification_results.append({
                        'link': qr,
                        'pdf_link': extracted_pdf_link,
                        'is_fetched': True,
                        'status': status
                    })
                else:
                    verification_results.append({
                        'link': qr,
                        'pdf_link': extracted_pdf_link,
                        'is_fetched': False,
                        'status': 'Not Verified'
                    })
            else:
                verification_results.append({
                    'link': qr,
                    'pdf_link': None,
                    'is_fetched': False,
                    'status': 'Not Verified'
                })
    else:
        # No QR codes found, use extracted link
        extracted_pdf_link = extract_link(pdf_bytes)
        verification_results = []
        if extracted_pdf_link:
            fetched_pdf = download_pdf(extracted_pdf_link)
            if fetched_pdf:
                fetched_pdf_text = extract_text_from_pdf(fetched_pdf)
                fetched_name, fetched_marks, _, _ = extract_name_and_scores(fetched_pdf_text)
                status = 'Verified' if (original_name == fetched_name and original_marks == fetched_marks) else 'Not Verified'
                verification_results.append({
                    'link': None,
                    'pdf_link': extracted_pdf_link,
                    'is_fetched': True,
                    'status': status
                })
            else:
                verification_results.append({
                    'link': None,
                    'pdf_link': extracted_pdf_link,
                    'is_fetched': False,
                    'status': 'Not Verified'
                })
        else:
            verification_results.append({
                'link': None,
                'pdf_link': None,
                'is_fetched': False,
                'status': 'Not Verified'
            })

    return {
        'name': original_name,
        'marks': original_marks,
        'assignment_score': assignment_score,
        'proctored_score': proctored_score,
        'verification_results': verification_results,
        'pdf_link': extracted_pdf_link if extracted_pdf_link else None
    }

def process_certificates(uploaded_files):
    results_list = []
    my_bar = st.progress(0)  # Progress bar
    total_files = len(uploaded_files)
    for i, uploaded_file in enumerate(uploaded_files):
        file_bytes = uploaded_file.read()
        results = process_pdf(file_bytes)
        results_list.append({
            'Filename': uploaded_file.name,
            'Name': results['name'],
            'Assignment Score (out of 25)': results['assignment_score'],
            'Proctored Exam Score (out of 75)': results['proctored_score'],
            'Marks (%)': results['marks'],
            'Status': any(result['status'] == 'Verified' for result in results['verification_results']),
            'links for pdf': results['pdf_link']
        })
        my_bar.progress((i + 1) / total_files)

    df = pd.DataFrame(results_list)
    df['Status'] = df['Status'].apply(lambda x: 'Verified' if x else 'Not Verified')
    df = df.sort_values(by='Status', ascending=False) 
    return df

# Streamlit Interface
st.title("🎓 Certificate Verification Interface")
page = st.sidebar.radio("📄 Select a page", ["Home", "Bulk Verification", "Single Certificate Verification"])

if page == "Home":
    st.write("Welcome to the NPTEL Certificate Verification Interface.")
    st.image("https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExODVveGQyam9oc2FocXgzYW1ieWt1Zzd6dThiMmEzeHd6eXdxN3FhaiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/coxQHKASG60HrHtvkt/giphy.gif", use_column_width=True)

elif page == "Bulk Verification":
    st.header("📁 Bulk Certificate Verification")
    uploaded_files = st.file_uploader("Upload a folder of certificates", accept_multiple_files=True, type=['pdf'])
    if uploaded_files:
        st.write("🔄 Processing...")
        results_df = process_certificates(uploaded_files)
        st.success("✔️ Processing completed!")
        st.write(results_df)

elif page == "Single Certificate Verification":
    st.header("📄 Single Certificate Verification")
    uploaded_file = st.file_uploader("Upload a single certificate", type=['pdf'])
    if uploaded_file:
        st.write("🔄 Processing...")
        file_bytes = uploaded_file.read()
        results = process_pdf(file_bytes)
        st.success("✔️ Verification completed!")
        st.write(f"Name: {results['name']}")
        st.write(f"Marks: {results['marks']}")
        st.write(f"Assignment Score: {results['assignment_score']}")
        st.write(f"Proctored Exam Score: {results['proctored_score']}")
        st.write(f"PDF Link: {results['pdf_link']}")
        for result in results['verification_results']:
            st.write(f"Verified PDF Link: {result['pdf_link']}")
            st.write(f"Status: {result['status']}")
