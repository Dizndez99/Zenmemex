kontolmu kecil jika tidak dibaca

Zenmemex

Zenmemex adalah skrip otomatisasi untuk jaringan Zenchain, mendukung transaksi, deployment kontrak pintar, dan pengelolaan token.

Fitur

Kirim native token ke alamat acak.

Deploy kontrak pintar sederhana.

Buat dan kelola token ERC-20 (DEZ).

Berjalan otomatis setiap 10 detik.


Instalasi

1. Clone repository:

git clone https://github.com/Dizndez99/Zenmemex.git  
cd Zenmemex


2. Instal dependensi:

pip install -r requirements.txt


3. Konfigurasi file .env:

nano .env

Tambahkan:

RPC_URL=https://zenchain-testnet.api.onfinality.io/public  
ACCOUNT_ADDRESS=0xYourAccountAddress  
PRIVATE_KEY=YourPrivateKey


4. Jalankan skrip:

python3 app.py  atau
python3 main.py




---

Cara Kerja

Kirim 0.0001 native token ke alamat acak.

Deploy kontrak pintar.

Buat token DEZ dan kirim ke alamat acak.

Burn 10 token DEZ.

Proses berulang setiap 10 detik.



---

