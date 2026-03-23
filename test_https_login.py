import urllib.request
import urllib.parse
import http.cookiejar
import ssl

def test_http_login(username, password):
    url = "https://127.0.0.1:5000/login"
    data = urllib.parse.urlencode({
        "username": username,
        "password": password
    }).encode("utf-8")
    
    cj = http.cookiejar.CookieJar()
    # Custom opener with SSL context
    context = ssl._create_unverified_context()
    https_handler = urllib.request.HTTPSHandler(context=context)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), https_handler)
    
    try:
        req = urllib.request.Request(url, data=data)
        response = opener.open(req)
        
        final_url = response.geturl()
        print(f"Status Code: {response.getcode()}")
        print(f"Final URL: {final_url}")
        
        if "dashboard" in final_url:
            print(f"Login successful for '{username}'! Redirected to dashboard.")
        else:
            print(f"Login failed for '{username}'. Stayed on or redirected elsewhere.")
            body = response.read().decode("utf-8")
            if "Invalid username or password" in body:
                print("Error message found: Invalid username or password")
            else:
                print("No standard error message found in response.")
                print(f"Body snippet: {body[:200]}")
    
    except Exception as e:
        print(f"An error occurred during HTTP request: {e}")

if __name__ == "__main__":
    test_http_login('student1', 'student123')
