def test_home_has_seo_tags(client):
    html = client.get("/").text
    assert '<link rel="canonical"' in html
    assert 'property="og:image"' in html and "/og.png" in html
    assert 'name="twitter:card"' in html
    assert "application/ld+json" in html and '"@type": "Person"' in html


def test_sitemap(client):
    r = client.get("/sitemap.xml")
    assert r.status_code == 200
    assert "application/xml" in r.headers["content-type"]
    for p in ("/workshop", "/dashboard", "/contact"):
        assert f"{p}</loc>" in r.text


def test_contact_page(client):
    r = client.get("/contact")
    assert r.status_code == 200
    assert "pradyumnaprasad.05@gmail.com" in r.text
    assert "leetcode.com/u/Pradyumna_Prasad" in r.text


def test_robots_points_to_sitemap(client):
    r = client.get("/robots.txt")
    assert r.status_code == 200
    assert "Sitemap:" in r.text and "sitemap.xml" in r.text


def test_og_image(client):
    r = client.get("/og.png")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert r.content[:4] == b"\x89PNG"


def test_security_headers(client):
    h = client.get("/").headers
    assert h["x-content-type-options"] == "nosniff"
    assert h["referrer-policy"] == "strict-origin-when-cross-origin"


def test_themed_404_for_pages(client):
    r = client.get("/no-such-page")
    assert r.status_code == 404
    assert "off the edge of the map" in r.text


def test_json_404_for_api(client):
    r = client.get("/api/nope")
    assert r.status_code == 404
    assert r.json()["detail"] == "Not Found"
