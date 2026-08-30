import requests

url = "http://127.0.0.1:8000/api/documents/"
data = {
    "organization": "00000000-0000-0000-0000-000000000001",
    "doc_type": "sales_rfp"
}
# We don't have a real file, just send some data
files = {'file': ('test.pdf', b'fake pdf data', 'application/pdf')}
response = requests.post(url, data=data, files=files)

print("Status:", response.status_code)
print("Body:", response.text)
