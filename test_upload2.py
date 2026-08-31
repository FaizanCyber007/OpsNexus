import requests

url = "http://127.0.0.1:8000/api/documents/"
data = {
    "organization": "00000000-0000-0000-0000-000000000001",
    "doc_type": "other"
}
# Send fake text file to simulate an invoice
files = {'file': ('test_invoice.txt', b'Acme Corporation invoice PO-1042 total $10,000.00', 'text/plain')}
response = requests.post(url, data=data, files=files)

print("Status:", response.status_code)
print("Body:", response.text)
