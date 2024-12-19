Berikut adalah README versi lebih simpel:

# Zenmemex  

Zenmemex adalah skrip otomatisasi untuk jaringan **Zenchain**, dirancang untuk melakukan transaksi, deployment kontrak pintar, dan pengelolaan token secara otomatis.  

## Fitur  
- Kirim native token ke alamat acak.  
- Deploy kontrak pintar sederhana.  
- Buat dan kelola token ERC-20 (DEZ).  
- Otomatisasi proses setiap 10 detik.  

## Cara Instalasi  

1. **Clone Repository**  
   ```bash  
   git clone https://github.com/Dizndez99/Zenmemex.git  
   cd Zenmemex

2. Instal Dependensi

pip install -r requirements.txt


3. Konfigurasi
Buat file .env dengan format:

nano .env

RPC_URL=https://zenchain-testnet.api.onfinality.io/public  
ACCOUNT_ADDRESS=0xYourAccountAddress  
PRIVATE_KEY=YourPrivateKey


4. Jalankan Skrip

python app.py



Cara Kerja

Kirim 0.0001 native token.

Deploy kontrak pintar.

Buat token DEZ dan kirim ke alamat acak.

Burn 10 token DEZ.

Ulangi setiap 10 detik


