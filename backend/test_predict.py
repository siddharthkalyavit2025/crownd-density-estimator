"""Quick test script for the /api/predict endpoint."""
import urllib.request
import json
import http.client

# Download a test crowd image
img_url = "https://images.unsplash.com/photo-1506157786151-b8491531f063?auto=format&fit=crop&w=400&q=60"
urllib.request.urlretrieve(img_url, "test_crowd.jpg")
print("Downloaded test image")

# Build multipart form data
boundary = "----TestBoundary7MA4YWxk"
body = b""
body += ("------TestBoundary7MA4YWxk\r\n").encode()
body += ('Content-Disposition: form-data; name="image"; filename="test_crowd.jpg"\r\n').encode()
body += b"Content-Type: image/jpeg\r\n\r\n"
with open("test_crowd.jpg", "rb") as f:
    body += f.read()
body += b"\r\n------TestBoundary7MA4YWxk--\r\n"

# Send request
conn = http.client.HTTPConnection("127.0.0.1", 5000)
headers = {"Content-Type": "multipart/form-data; boundary=----TestBoundary7MA4YWxk"}
conn.request("POST", "/api/predict", body, headers)
resp = conn.getresponse()
data = json.loads(resp.read())
print(json.dumps(data, indent=2))
