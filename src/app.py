import requests
import xml.etree.ElementTree as ET
import time
from flask import Flask, jsonify, request
from datetime import datetime
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

# Hardcoded szoftver adatok
SOFTWARE_DATA = {
    "softwareId": "123456789123456789",
    "softwareName": "NavInvoiceAPI",
    "softwareOperation": "ONLINE_SERVICE",
    "softwareMainVersion": "1.0",
    "softwareDevName": "YourCompany",
    "softwareDevContact": "contact@yourcompany.com",
    "softwareDevCountryCode": "HU",
    "softwareDevTaxNumber": "12345678"
}

# NAV API konfiguráció
API_URL = os.getenv("NAV_API_URL", "https://api-test.onlineszamla.nav.gov.hu/invoiceService/v3")
NS = {"ns": "http://schemas.nav.gov.hu/OSA/3.0/api"}

def get_token(user_data):
    """Token lekérése a NAV API-tól"""
    token_url = f"{API_URL}/tokenExchange"
    headers = {"Content-Type": "application/xml", "Accept": "application/xml"}
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <TokenExchangeRequest xmlns="http://schemas.nav.gov.hu/OSA/3.0/api">
        <header>
            <requestId>{datetime.now().strftime('%Y%m%d%H%M%S%f')}</requestId>
            <timestamp>{datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}</timestamp>
            <requestVersion>3.0</requestVersion>
            <headerVersion>1.0</headerVersion>
        </header>
        <user>
            <login>{user_data['login']}</login>
            <passwordHash>{user_data['password']}</passwordHash>
            <taxNumber>{user_data['taxNumber']}</taxNumber>
            <requestSignature>{user_data['signKey']}</requestSignature>
        </user>
        <software>{format_software_data()}</software>
    </TokenExchangeRequest>"""
    
    response = requests.post(token_url, headers=headers, data=xml)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    token = root.find(".//ns:encodedExchangeToken", NS).text
    return token

def format_software_data():
    """Szoftver adatok XML formátumba"""
    return f"""
        <softwareId>{SOFTWARE_DATA['softwareId']}</softwareId>
        <softwareName>{SOFTWARE_DATA['softwareName']}</softwareName>
        <softwareOperation>{SOFTWARE_DATA['softwareOperation']}</softwareOperation>
        <softwareMainVersion>{SOFTWARE_DATA['softwareMainVersion']}</softwareMainVersion>
        <softwareDevName>{SOFTWARE_DATA['softwareDevName']}</softwareDevName>
        <softwareDevContact>{SOFTWARE_DATA['softwareDevContact']}</softwareDevContact>
        <softwareDevCountryCode>{SOFTWARE_DATA['softwareDevCountryCode']}</softwareDevCountryCode>
        <softwareDevTaxNumber>{SOFTWARE_DATA['softwareDevTaxNumber']}</softwareDevTaxNumber>
    """

@app.route("/api/invoices", methods=["GET"])
def get_invoices():
    # API kulcs ellenőrzése
    api_key = os.getenv("API_KEY")
    if request.args.get("api_key") != api_key:
        return jsonify({"status": "error", "message": "Invalid API key"}), 401

    # Felhasználói adatok kinyerése a query paraméterekből
    required_params = ["login", "password", "taxNumber", "signKey", "exchangeKey"]
    user_data = {}
    for param in required_params:
        if param not in request.args:
            return jsonify({"status": "error", "message": f"Missing parameter: {param}"}), 400
        user_data[param] = request.args.get(param)

    try:
        token = get_token(user_data)
        headers = {
            "Content-Type": "application/xml",
            "Accept": "application/xml",
            "Authorization": f"Bearer {token}"
        }
        
        all_invoices = []
        page = 1
        query_url = f"{API_URL}/queryInvoiceDigest"
        
        while True:
            xml = f"""<?xml version="1.0" encoding="UTF-8"?>
            <QueryInvoiceDigestRequest xmlns="http://schemas.nav.gov.hu/OSA/3.0/api">
                <header>
                    <requestId>{datetime.now().strftime('%Y%m%d%H%M%S%f')}</requestId>
                    <timestamp>{datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}</timestamp>
                    <requestVersion>3.0</requestVersion>
                    <headerVersion>1.0</headerVersion>
                </header>
                <user>
                    <login>{user_data['login']}</login>
                    <passwordHash>{user_data['password']}</passwordHash>
                    <taxNumber>{user_data['taxNumber']}</taxNumber>
                    <requestSignature>{user_data['signKey']}</requestSignature>
                </user>
                <software>{format_software_data()}</software>
                <page>{page}</page>
                <invoiceQueryParams>
                    <mandatoryQueryParams>
                        <invoiceIssueDate>
                            <dateFrom>2025-04-01</dateFrom>
                            <dateTo>2025-04-30</dateTo>
                        </invoiceIssueDate>
                    </mandatoryQueryParams>
                    <invoiceDirection>OUTBOUND</invoiceDirection>
                </invoiceQueryParams>
            </QueryInvoiceDigestRequest>"""
            
            response = requests.post(query_url, headers=headers, data=xml)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            invoice_digests = root.findall(".//ns:invoiceDigest", NS)
            
            for invoice in invoice_digests:
                all_invoices.append({
                    "invoiceNumber": invoice.find("ns:invoiceNumber", NS).text,
                    "invoiceOperation": invoice.find("ns:invoiceOperation", NS).text,
                    "invoiceCategory": invoice.find("ns:invoiceCategory", NS).text,
                    "invoiceIssueDate": invoice.find("ns:invoiceIssueDate", NS).text,
                    "supplierTaxNumber": invoice.find("ns:supplierTaxNumber", NS).text,
                    "supplierName": invoice.find("ns:supplierName", NS).text,
                    "customerTaxNumber": invoice.find("ns:customerTaxNumber", NS).text if invoice.find("ns:customerTaxNumber", NS) is not None else None,
                    "customerName": invoice.find("ns:customerName", NS).text if invoice.find("ns:customerName", NS) is not None else None,
                    "paymentMethod": invoice.find("ns:paymentMethod", NS).text,
                    "paymentDate": invoice.find("ns:paymentDate", NS).text,
                    "invoiceAppearance": invoice.find("ns:invoiceAppearance", NS).text,
                    "source": invoice.find("ns:source", NS).text,
                    "invoiceDeliveryDate": invoice.find("ns:invoiceDeliveryDate", NS).text,
                    "currency": invoice.find("ns:currency", NS).text,
                    "invoiceNetAmount": float(invoice.find("ns:invoiceNetAmount", NS).text),
                    "invoiceNetAmountHUF": float(invoice.find("ns:invoiceNetAmountHUF", NS).text),
                    "invoiceVatAmount": float(invoice.find("ns:invoiceVatAmount", NS).text),
                    "invoiceVatAmountHUF": float(invoice.find("ns:invoiceVatAmountHUF", NS).text),
                    "transactionId": invoice.find("ns:transactionId", NS).text,
                    "index": int(invoice.find("ns:index", NS).text),
                    "insDate": invoice.find("ns:insDate", NS).text,
                    "completenessIndicator": invoice.find("ns:completenessIndicator", NS).text == "true",
                    "originalInvoiceNumber": invoice.find("ns:originalInvoiceNumber", NS).text if invoice.find("ns:originalInvoiceNumber", NS) is not None else None,
                    "modificationIndex": int(invoice.find("ns:modificationIndex", NS).text) if invoice.find("ns:modificationIndex", NS) is not None else None
                })
            
            available_pages = int(root.find(".//ns:availablePage", NS).text)
            if page >= available_pages:
                break
            page += 1
            time.sleep(1)  # NAV rate limit miatt
            
        return jsonify({
            "status": "success",
            "data": all_invoices,
            "total": len(all_invoices)
        })

    except Exception as ex:
        return jsonify({
            "status": "error",
            "message": f"{type(ex).__name__}: {str(ex)}"
        }), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)