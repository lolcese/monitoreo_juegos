from requests_tor import RequestsTor

# If you use the Tor
rt = RequestsTor(tor_ports=(9050,), tor_cport=9051)

url = 'https://httpbin.org/anything'
r = rt.get(url)
print(r.text)

urls = ['https://foxnews.com', 'https://nbcnews.com', 'https://wsj.com/news/world',
        'https://abcnews.go.com', 'https://cbsnews.com',  'https://nytimes.com',
        'https://usatoday.com','https://reuters.com/world', 'http://bbc.com/news',
        'https://theguardian.com/world', 'https://cnn.com', 'https://apnews.com']
r = rt.get_urls(urls)
print(r[-1].text)