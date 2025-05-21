from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime
import xml.etree.ElementTree as ET
import hashlib
import base64

app = Flask(__name__)
CORS(app)

def generate_request_signature(login, sign_key, timestamp, request_id):
    """Kérés aláírás generálása"""
    string_to_hash = f"{login}{timestamp}{sign_key}"
    return hashlib.sha3_512(string_to_hash.encode()).hexdigest()

def create_request_xml(user_data, date_from, date_to, page, direction):
    """XML kérés létrehozása"""
    root = ET.Element("QueryInvoiceDigestRequest")
    
    # Header
    header = ET.SubElement(root, "header")
    ET.SubElement(header, "requestId").text = "REQ-" + datetime.now().strftime("%Y%m%d%H%M%S")
    ET.SubElement(header, "timestamp").text = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    ET.SubElement(header, "requestVersion").text = "3.0"
    ET.SubElement(header, "headerVersion").text = "1.0"
    
    # User
    user = ET.SubElement(root, "user")
    ET.SubElement(user, "login").text = user_data['login']
    ET.SubElement(user, "passwordHash").text = hashlib.sha512(user_data['password'].encode()).hexdigest()
    ET.SubElement(user, "taxNumber").text = user_data['tax_number']
    ET.SubElement(user, "requestSignature").text = generate_request_signature(
        user_data['login'],
        user_data['sign_key'],
        datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "REQ-" + datetime.now().strftime("%Y%m%d%H%M%S")
    )
    
    # Query params
    ET.SubElement(root, "page").text = str(page)
    ET.SubElement(root, "invoiceDirection").text = direction
    
    invoice_query_params = ET.SubElement(root, "invoiceQueryParams")
    mandatory_params = ET.SubElement(invoice_query_params, "mandatoryQueryParams")
    issue_date = ET.SubElement(mandatory_params, "invoiceIssueDate")
    ET.SubElement(issue_date, "dateFrom").text = date_from
    ET.SubElement(issue_date, "dateTo").text = date_to
    
    return ET.tostring(root, encoding='unicode')

@app.route('/query_invoice', methods=['POST'])
def query_invoice():
    try:
        # JSON adatok beolvasása
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON input'}), 400

        # Paraméterek kinyerése
        user_data = data.get('userData')
        date_from = data.get('dateFrom')
        date_to = data.get('dateTo')
        direction = data.get('direction', 'OUTBOUND')
        page = data.get('page', 1)
        api_url = data.get('apiUrl', 'https://api-test.onlineszamla.nav.gov.hu/invoiceService')

        # Kötelező paraméterek ellenőrzése
        if not all([user_data, date_from, date_to]):
            return jsonify({'error': 'Hiányzó kötelező paraméterek'}), 400

        # User data ellenőrzése
        required_user_fields = ['login', 'password', 'tax_number', 'sign_key']
        if not all(field in user_data for field in required_user_fields):
            return jsonify({'error': 'Hiányzó user data mezők'}), 400

        # XML kérés létrehozása
        request_xml = create_request_xml(user_data, date_from, date_to, page, direction)

        # NAV API hívás
        headers = {
            'Content-Type': 'application/xml',
            'Accept': 'application/xml'
        }
        
        response = requests.post(
            f"{api_url}/queryInvoiceDigest",
            data=request_xml,
            headers=headers
        )

        if response.status_code != 200:
            return jsonify({'error': f'NAV API hiba: {response.text}'}), 500

        # XML válasz feldolgozása
        root = ET.fromstring(response.content)
        invoice_digest_result = root.find('.//invoiceDigestResult')

        # Válasz összeállítása
        result = {
            'success': True,
            'data': {
                'currentPage': int(invoice_digest_result.find('currentPage').text),
                'availablePage': int(invoice_digest_result.find('availablePage').text),
                'invoices': []
            }
        }

        # Számlák feldolgozása
        for invoice in invoice_digest_result.findall('.//invoiceDigest'):
            result['data']['invoices'].append({
                'invoiceNumber': invoice.find('invoiceNumber').text,
                'customerName': invoice.find('customerName').text,
                'customerTaxNumber': invoice.find('customerTaxNumber').text,
                'invoiceIssueDate': invoice.find('invoiceIssueDate').text,
                'invoiceNetAmountHUF': float(invoice.find('invoiceNetAmountHUF').text),
                'invoiceVatAmountHUF': float(invoice.find('invoiceVatAmountHUF').text),
                'supplierName': invoice.find('supplierName').text,
                'supplierTaxNumber': invoice.find('supplierTaxNumber').text,
                'transactionId': invoice.find('transactionId').text
            })

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000))) 