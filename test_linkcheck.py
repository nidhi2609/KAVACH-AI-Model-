from linkcheck import check_url, find_links


def test_fake_bank_link_is_high():
    assert check_url("https://sbi-kyc-update.xyz/login")["score"] >= 60


def test_official_links_clean():
    assert check_url("https://www.sbi.co.in")["score"] == 0
    assert check_url("https://cybercrime.gov.in")["score"] == 0


def test_lookalike_of_gov_domain_not_trusted():
    assert check_url("https://cybercrime.gov.in.evil.com")["score"] >= 30


def test_ip_shortener_apk():
    assert check_url("http://192.168.1.1/pay")["score"] >= 40
    assert check_url("https://bit.ly/abc")["level"] == "Suspicious"
    assert check_url("https://files.example.com/app.apk")["score"] >= 50


def test_invalid_and_empty():
    assert check_url("")["level"] == "Not a valid link"
    assert check_url("hello")["level"] == "Not a valid link"


def test_find_links():
    ls = find_links("Pay at www.sbi-kyc.xyz/login now. Also see cybercrime.gov.in.")
    assert ls == ["www.sbi-kyc.xyz/login", "cybercrime.gov.in"]
