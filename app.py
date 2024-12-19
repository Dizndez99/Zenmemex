from web3 import Web3
import time
import os
import secrets
from dotenv import load_dotenv
from datetime import datetime
from colorama import Fore, Style, init
from solcx import install_solc, set_solc_version, compile_source

# Initialize Colorama
init(autoreset=True)

# Symbols and Colors
CHECK_MARK = Fore.GREEN + "✔️" + Style.RESET_ALL
CROSS_MARK = Fore.RED + "❌" + Style.RESET_ALL
BALANCE_SYMBOL = Fore.CYAN + "💰" + Style.RESET_ALL
ZEN_SYMBOL = Fore.YELLOW + "ZCX" + Style.RESET_ALL
TOKEN_SYMBOL = Fore.MAGENTA + "DEZ" + Style.RESET_ALL

# Load Environment Variables
load_dotenv()

# Solidity Configuration
install_solc('0.8.0')
set_solc_version('0.8.0')

# Blockchain Configuration
RPC_URL = os.getenv('RPC_URL', "https://zenchain-testnet.api.onfinality.io/public")
CHAIN_ID = 8408
web3 = Web3(Web3.HTTPProvider(RPC_URL))

# Smart Contract Source Code
STORAGE_CONTRACT_SOURCE = '''
pragma solidity ^0.8.0;

contract SimpleStorage {
    uint256 storedData;

    constructor() {
        storedData = 100;
    }

    function set(uint256 x) public {
        storedData = x;
    }

    function get() public view returns (uint256) {
        return storedData;
    }
}
'''

# Token Contract Source Code
TOKEN_CONTRACT_SOURCE = '''
pragma solidity ^0.8.0;

interface IERC20 {
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address recipient, uint256 amount) external returns (bool);
    function burn(uint256 amount) external returns (bool);
    event Transfer(address indexed from, address indexed to, uint256 value);
}

contract DezToken is IERC20 {
    string public name = "Dez Token";
    string public symbol = "DEZ";
    uint8 public decimals = 18;
    uint256 private _totalSupply;
    mapping(address => uint256) private _balances;

    constructor(uint256 initialSupply) {
        _mint(msg.sender, initialSupply * 10**uint256(decimals));
    }

    function totalSupply() external view override returns (uint256) {
        return _totalSupply;
    }

    function balanceOf(address account) external view override returns (uint256) {
        return _balances[account];
    }

    function transfer(address recipient, uint256 amount) external override returns (bool) {
        require(_balances[msg.sender] >= amount, "Insufficient balance");
        _balances[msg.sender] -= amount;
        _balances[recipient] += amount;
        emit Transfer(msg.sender, recipient, amount);
        return true;
    }

    function burn(uint256 amount) external override returns (bool) {
        require(_balances[msg.sender] >= amount, "Insufficient balance");
        _balances[msg.sender] -= amount;
        _totalSupply -= amount;
        emit Transfer(msg.sender, address(0), amount);
        return true;
    }

    function _mint(address account, uint256 amount) internal {
        _totalSupply += amount;
        _balances[account] = amount;
        emit Transfer(address(0), account, amount);
    }
}
'''

class TokenManager:
    def __init__(self, web3):
        self.web3 = web3
        self.token_contract = None
        self.token_address = None

    def deploy_token(self, account_address, private_key, initial_supply):
        try:
            compiled_sol = compile_source(TOKEN_CONTRACT_SOURCE)
            contract_interface = compiled_sol['<stdin>:DezToken']

            DezToken = self.web3.eth.contract(
                abi=contract_interface['abi'], 
                bytecode=contract_interface['bin']
            )
            
            transaction = DezToken.constructor(initial_supply).build_transaction({
                'from': account_address,
                'nonce': self.web3.eth.get_transaction_count(account_address),
                'gas': 2000000,
                'gasPrice': self.web3.eth.gas_price
            })
            
            signed_tx = self.web3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            self.token_address = tx_receipt.contractAddress
            self.token_contract = self.web3.eth.contract(address=self.token_address, abi=contract_interface['abi'])

            print(Fore.GREEN + f"Token {TOKEN_SYMBOL} berhasil di-deploy di {self.token_address} {CHECK_MARK}")
            return True

        except Exception as e:
            print(Fore.RED + f"Gagal deploy token: {str(e)} {CROSS_MARK}")
            return False

    def send_token(self, from_address, private_key, to_address, amount):
        try:
            transaction = self.token_contract.functions.transfer(
                to_address, 
                int(amount * 10**18)
            ).build_transaction({
                'from': from_address,
                'nonce': self.web3.eth.get_transaction_count(from_address),
                'gas': 200000,
                'gasPrice': self.web3.eth.gas_price
            })

            signed_tx = self.web3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            self.web3.eth.wait_for_transaction_receipt(tx_hash)

            print(Fore.GREEN + f"Token {TOKEN_SYMBOL} berhasil dikirim ke {to_address} {CHECK_MARK}")
            return True

        except Exception as e:
            print(Fore.RED + f"Gagal mengirim token: {str(e)} {CROSS_MARK}")
            return False

    def burn_token(self, from_address, private_key, amount):
        try:
            transaction = self.token_contract.functions.burn(
                int(amount * 10**18)
            ).build_transaction({
                'from': from_address,
                'nonce': self.web3.eth.get_transaction_count(from_address),
                'gas': 200000,
                'gasPrice': self.web3.eth.gas_price
            })

            signed_tx = self.web3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            self.web3.eth.wait_for_transaction_receipt(tx_hash)

            print(Fore.GREEN + f"{TOKEN_SYMBOL} {amount} berhasil dibakar {CHECK_MARK}")
            return True

        except Exception as e:
            print(Fore.RED + f"Gagal membakar token: {str(e)} {CROSS_MARK}")
            return False

def check_connection():
    if web3.is_connected():
        print(Fore.GREEN + f"Terkoneksi dengan jaringan Zenchain Testnet {CHECK_MARK}")
        return True
    else:
        print(Fore.RED + f"Gagal terhubung ke jaringan Zenchain Testnet {CROSS_MARK}")
        return False

def get_balance(address):
    return web3.from_wei(web3.eth.get_balance(address), 'ether')

def deploy_storage_contract(account_address, private_key):
    try:
        compiled_sol = compile_source(STORAGE_CONTRACT_SOURCE)
        contract_interface = compiled_sol['<stdin>:SimpleStorage']

        SimpleStorage = web3.eth.contract(
            abi=contract_interface['abi'],
            bytecode=contract_interface['bin']
        )

        transaction = SimpleStorage.constructor().build_transaction({
            'from': account_address,
            'nonce': web3.eth.get_transaction_count(account_address),
            'gas': 2000000,
            'gasPrice': web3.eth.gas_price
        })

        signed_tx = web3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        print(Fore.GREEN + f"Storage Contract berhasil di-deploy di {tx_receipt.contractAddress} {CHECK_MARK}")
        return tx_receipt.contractAddress

    except Exception as e:
        print(Fore.RED + f"Gagal deploy storage contract: {str(e)} {CROSS_MARK}")
        return None

def send_native_token(sender_address, private_key, receiver_address, amount):
    try:
        transaction = {
            'nonce': web3.eth.get_transaction_count(sender_address),
            'to': receiver_address,
            'value': web3.to_wei(amount, 'ether'),
            'gas': 21000,
            'gasPrice': web3.eth.gas_price,
            'chainId': CHAIN_ID
        }

        signed_tx = web3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        web3.eth.wait_for_transaction_receipt(tx_hash)

        print(Fore.GREEN + f"Native token berhasil dikirim ke {receiver_address} {CHECK_MARK}")
        return True

    except Exception as e:
        print(Fore.RED + f"Gagal mengirim native token: {str(e)} {CROSS_MARK}")
        return False

def load_accounts():
    accounts = []
    index = 1
    while True:
        address = os.getenv(f'ACCOUNT_ADDRESS_{index}')
        private_key = os.getenv(f'PRIVATE_KEY_{index}')
        if not address or not private_key:
            break
        accounts.append((web3.to_checksum_address(address), private_key))
        index += 1
    return accounts

def main():
    if not check_connection():
        return

    accounts = load_accounts()
    if not accounts:
        print(Fore.RED + "Tidak ada akun yang ditemukan di file .env")
        return

    token_manager = TokenManager(web3)

    print(Fore.CYAN + "\nMemulai proses deployment token DEZ...")
    token_manager.deploy_token(accounts[0][0], accounts[0][1], 1000000)

    try:
        while True:
            for sender_address, private_key in accounts:
                print("\n" + Fore.YELLOW + "=" * 50)
                print(Fore.CYAN + f"Memproses akun: {sender_address}")

                random_receiver = web3.eth.account.create()
                print(Fore.CYAN + f"Alamat penerima acak: {random_receiver.address}")

                initial_balance = get_balance(sender_address)
                print(Fore.BLUE + f"{BALANCE_SYMBOL} Saldo Awal: {initial_balance} {ZEN_SYMBOL}")

                send_native_token(sender_address, private_key, random_receiver.address, 0.00001)
                deploy_storage_contract(sender_address, private_key)
                token_manager.send_token(sender_address, private_key, random_receiver.address, 100)
                token_manager.burn_token(sender_address, private_key, 10)

                final_balance = get_balance(sender_address)
                print(Fore.BLUE + f"{BALANCE_SYMBOL} Saldo Akhir: {final_balance} {ZEN_SYMBOL}")

                print(Fore.YELLOW + "=" * 50 + "\n")
                time.sleep(10)

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n🔴 Program dihentikan oleh user")
    except Exception as e:
        print(Fore.RED + f"\nTerjadi kesalahan: {str(e)}")

if __name__ == "__main__":
    main()
