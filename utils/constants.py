base_url = "https://sia.mercubuana.ac.id"
login_url = f"{base_url}/gate.php/login"
captcha_url = f"{base_url}/application/gate/libraries/kcaptcha/index.php"
home_url = f"{base_url}/akad.php/home"
jadwal_url = f"{base_url}/akad.php/biomhs/jadwal"
detail_url = f"{base_url}/akad.php/biomhs/lst"
print_transcript_url = f"{base_url}/akad.php/biomhs/cetaktranskrip"    

def get_transcript_url(username: str) -> str:
    return f"{base_url}/akad.php/biomhs/transkrip/{username}"