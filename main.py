from web3 import Web3
import time
import os
import secrets
from dotenv import load_dotenv
from datetime import datetime
from colorama import Fore, Style, init, Back
from solcx import install_solc, set_solc_version, compile_source

# Initialize Colorama
init(autoreset=True)

# Symbols and Colors
CHECK_MARK = Fore.GREEN + "✔️" + Style.RESET_ALL
CROSS_MARK = Fore.RED + "❌" + Style.RESET_ALL
BALANCE_SYMBOL = Fore.CYAN + "💰" + Style.RESET_ALL
ZEN_SYMBOL = Fore.YELLOW + "ZCX" + Style.RESET_ALL
TOKEN_SYMBOL = Fore.MAGENTA + "DEZ" + Style.RESET_ALL
NFT_SYMBOL = Fore.BLUE + "🎨" + Style.RESET_ALL

# Load Environment Variables
load_dotenv()

# Solidity Configuration
install_solc('0.8.0')
set_solc_version('0.8.0')

# Blockchain Configuration
RPC_URL = os.getenv('RPC_URL', "https://zenchain-testnet.api.onfinality.io/public")
CHAIN_ID = 8408
web3 = Web3(Web3.HTTPProvider(RPC_URL))

# Smart Contract Sources
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

TOKEN_CONTRACT_SOURCE = '''
pragma solidity ^0.8.0;

contract DezToken {
    string public name = "Dez Token";
    string public symbol = "DEZ";
    uint8 public decimals = 18;
    uint256 private _totalSupply;
    mapping(address => uint256) private _balances;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Mint(address indexed to, uint256 value);
    event Burn(address indexed from, uint256 value);

    constructor(uint256 initialSupply) {
        _mint(msg.sender, initialSupply * 10**uint256(decimals));
    }

    function totalSupply() external view returns (uint256) {
        return _totalSupply;
    }

    function balanceOf(address account) external view returns (uint256) {
        return _balances[account];
    }

    function transfer(address recipient, uint256 amount) external returns (bool) {
        require(_balances[msg.sender] >= amount, "Insufficient balance");
        _balances[msg.sender] -= amount;
        _balances[recipient] += amount;
        emit Transfer(msg.sender, recipient, amount);
        return true;
    }

    function burn(uint256 amount) external returns (bool) {
        require(_balances[msg.sender] >= amount, "Insufficient balance");
        _balances[msg.sender] -= amount;
        _totalSupply -= amount;
        emit Burn(msg.sender, amount);
        return true;
    }

    function mint(address to, uint256 amount) external returns (bool) {
        _mint(to, amount);
        return true;
    }

    function _mint(address account, uint256 amount) internal {
        _totalSupply += amount;
        _balances[account] += amount;
        emit Mint(account, amount);
    }
}
'''

NFT_CONTRACT_SOURCE = '''
pragma solidity ^0.8.0;

contract DezNFT {
    string public name = "Dez NFT";
    string public symbol = "DEZNFT";
    
    struct NFT {
        uint256 id;
        address owner;
        string uri;
    }
    
    mapping(uint256 => NFT) private _tokens;
    mapping(address => uint256[]) private _ownedTokens;
    uint256 private _tokenIdCounter;
    
    event Transfer(address indexed from, address indexed to, uint256 tokenId);
    event Mint(address indexed to, uint256 tokenId);
    event Burn(uint256 tokenId);
    
    function mint(address to, string memory uri) external returns (uint256) {
        uint256 tokenId = _tokenIdCounter;
        _tokenIdCounter++;
        
        _tokens[tokenId] = NFT(tokenId, to, uri);
        _ownedTokens[to].push(tokenId);
        
        emit Mint(to, tokenId);
        return tokenId;
    }
    
    function burn(uint256 tokenId) external {
        require(_tokens[tokenId].owner == msg.sender, "Not token owner");
        delete _tokens[tokenId];
        emit Burn(tokenId);
    }
    
    function transfer(address to, uint256 tokenId) external {
        require(_tokens[tokenId].owner == msg.sender, "Not token owner");
        _tokens[tokenId].owner = to;
        emit Transfer(msg.sender, to, tokenId);
    }
    
    function ownerOf(uint256 tokenId) external view returns (address) {
        return _tokens[tokenId].owner;
    }
}
'''

class TokenManager:
    def __init__(self, web3):
        self.web3 = web3
        self.token_contract = None
        self.token_address = None
        self.nft_contract = None
        self.nft_address = None

    def deploy_token(self, account_address, private_key, initial_supply):
        try:
            print(Fore.CYAN + "\n📝 Task 4: Deploying DEZ Token...")
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
            self.token_contract = self.web3.eth.contract(
                address=self.token_address,
                abi=contract_interface['abi']
            )

            print(Fore.GREEN + f"✨ Token {TOKEN_SYMBOL} deployed at {self.token_address} {CHECK_MARK}")
            return True

        except Exception as e:
            print(Fore.RED + f"Failed to deploy token: {str(e)} {CROSS_MARK}")
            return False

    def deploy_nft(self, account_address, private_key):
        try:
            print(Fore.CYAN + "\n📝 Task 5: Deploying DEZ NFT...")
            compiled_sol = compile_source(NFT_CONTRACT_SOURCE)
            contract_interface = compiled_sol['<stdin>:DezNFT']

            DezNFT = self.web3.eth.contract(
                abi=contract_interface['abi'],
                bytecode=contract_interface['bin']
            )

            transaction = DezNFT.constructor().build_transaction({
                'from': account_address,
                'nonce': self.web3.eth.get_transaction_count(account_address),
                'gas': 2000000,
                'gasPrice': self.web3.eth.gas_price
            })

            signed_tx = self.web3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

            self.nft_address = tx_receipt.contractAddress
            self.nft_contract = self.web3.eth.contract(
                address=self.nft_address,
                abi=contract_interface['abi']
            )

            print(Fore.GREEN + f"✨ NFT {NFT_SYMBOL} deployed at {self.nft_address} {CHECK_MARK}")
            return True

        except Exception as e:
            print(Fore.RED + f"Failed to deploy NFT: {str(e)} {CROSS_MARK}")
            return False

    def send_token(self, from_address, private_key, to_address, amount):
        try:
            print(Fore.CYAN + f"\n📝 Task 6: Sending {amount} {TOKEN_SYMBOL} to random address...")
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

            print(Fore.GREEN + f"✨ {amount} {TOKEN_SYMBOL} sent to {to_address} {CHECK_MARK}")
            return True

        except Exception as e:
            print(Fore.RED + f"Failed to send token: {str(e)} {CROSS_MARK}")
            return False

    def send_nft(self, from_address, private_key, to_address, token_id):
        try:
            print(Fore.CYAN + f"\n📝 Task 7: Sending NFT #{token_id} to random address...")
            transaction = self.nft_contract.functions.transfer(
                to_address,
                token_id
            ).build_transaction({
                'from': from_address,
                'nonce': self.web3.eth.get_transaction_count(from_address),
                'gas': 200000,
                'gasPrice': self.web3.eth.gas_price
            })

            signed_tx = self.web3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            self.web3.eth.wait_for_transaction_receipt(tx_hash)

            print(Fore.GREEN + f"✨ NFT #{token_id} sent to {to_address} {CHECK_MARK}")
            return True

        except Exception as e:
            print(Fore.RED + f"Failed to send NFT: {str(e)} {CROSS_MARK}")
            return False

    def burn_token(self, from_address, private_key, amount):
        try:
            print(Fore.CYAN + f"\n📝 Task 8: Burning {amount} {TOKEN_SYMBOL}...")
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

            print(Fore.GREEN + f"✨ {amount} {TOKEN_SYMBOL} burned {CHECK_MARK}")
            return True

        except Exception as e:
            print(Fore.RED + f"Failed to burn token: {str(e)} {CROSS_MARK}")
            return False

    def burn_nft(self, from_address, private_key, token_id):
        try:
            print(Fore.CYAN + f"\n📝 Task 9: Burning NFT #{token_id}...")
            transaction = self.nft_contract.functions.burn(token_id).build_transaction({
                'from': from_address,
                'nonce': self.web3.eth.get_transaction_count(from_address),
                'gas': 200000,
                'gasPrice': self.web3.eth.gas_price
            })

            signed_tx = self.web3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            self.web3.eth.wait_for_transaction_receipt(tx_hash)

            print(Fore.GREEN + f"✨ NFT #{token_id} burned {CHECK_MARK}")
            return True

        except Exception as e:
            print(Fore.RED + f"Failed to burn NFT: {str(e)} {CROSS_MARK}")
            return False

    def mint_token(self, from_address, private_key, amount):
        try:
            print(Fore.CYAN + f"\n📝 Task 10: Minting {amount} {TOKEN_SYMBOL}...")
            transaction = self.token_contract.functions.mint(
                from_address,
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

            print(Fore.GREEN + f"✨ {amount} {TOKEN_SYMBOL} minted {CHECK_MARK}")
            return True

        except Exception as e:
            print(Fore.RED + f"Failed to mint token: {str(e)} {CROSS_MARK}")
            return False

    def mint_nft(self, from_address, private_key, uri):
        try:
            print(Fore.CYAN + "\n📝 Task 11: Minting new NFT...")
            transaction = self.nft_contract.functions.mint(
                from_address,
                uri
            ).build_transaction({
                'from': from_address,
                'nonce': self.web3.eth.get_transaction_count(from_address),
                'gas': 200000,
                'gasPrice': self.web3.eth.gas_price
            })

            signed_tx = self.web3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            token_id = len(self._get_owned_tokens(from_address))

            print(Fore.GREEN + f"✨ NFT #{token_id} minted {CHECK_MARK}")
            return token_id

        except Exception as e:
            print(Fore.RED + f"Failed to mint NFT: {str(e)} {CROSS_MARK}")
            return None

    def _get_owned_tokens(self, address):
        try:
            return self.nft_contract.functions.getOwnedTokens(address).call()
        except:
            return []

def check_connection():
    try:
        if web3.is_connected():
            print(Fore.GREEN + f"\n🌐 Connected to Zenchain Testnet {CHECK_MARK}")
            current_block = web3.eth.block_number
            print(Fore.CYAN + f"📦 Current Block: {current_block}")
            return True
        else:
            print(Fore.RED + f"\n❌ Failed to connect to Zenchain Testnet {CROSS_MARK}")
            return False
    except Exception as e:
        print(Fore.RED + f"\n❌ Connection error: {str(e)} {CROSS_MARK}")
        return False

def get_balance(address):
    balance = web3.from_wei(web3.eth.get_balance(address), 'ether')
    return float(balance)

def print_balance_info(address, balance, message=""):
    print(f"{BALANCE_SYMBOL} {message} Balance: {balance:.6f} {ZEN_SYMBOL}")
    print(Fore.CYAN + f"└── Address: {address}")

def deploy_storage_contract(account_address, private_key):
    try:
        print(Fore.CYAN + "\n📝 Task 3: Deploying Storage Contract...")
        compiled_sol = compile_source(STORAGE_CONTRACT_SOURCE)
        contract_interface = compiled_sol['<stdin>:SimpleStorage']

        Storage = web3.eth.contract(
            abi=contract_interface['abi'],
            bytecode=contract_interface['bin']
        )

        transaction = Storage.constructor().build_transaction({
            'from': account_address,
            'nonce': web3.eth.get_transaction_count(account_address),
            'gas': 2000000,
            'gasPrice': web3.eth.gas_price
        })

        signed_tx = web3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        print(Fore.GREEN + f"✨ Storage Contract deployed at {tx_receipt.contractAddress} {CHECK_MARK}")
        return tx_receipt.contractAddress

    except Exception as e:
        print(Fore.RED + f"Failed to deploy storage contract: {str(e)} {CROSS_MARK}")
        return None

def send_native_token(sender_address, private_key, amount=0.0001):
    try:
        print(Fore.CYAN + f"\n📝 Task 2: Sending {amount} {ZEN_SYMBOL} to random address...")
        
        # Generate random receiver address
        random_receiver = web3.eth.account.create()
        print(Fore.YELLOW + f"📤 Random receiver address: {random_receiver.address}")

        initial_balance = get_balance(sender_address)
        print_balance_info(sender_address, initial_balance, "Initial")

        transaction = {
            'nonce': web3.eth.get_transaction_count(sender_address),
            'to': random_receiver.address,
            'value': web3.to_wei(amount, 'ether'),
            'gas': 21000,
            'gasPrice': web3.eth.gas_price,
            'chainId': CHAIN_ID
        }

        signed_tx = web3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        web3.eth.wait_for_transaction_receipt(tx_hash)

        final_balance = get_balance(sender_address)
        print_balance_info(sender_address, final_balance, "Final")
        
        print(Fore.GREEN + f"✨ {amount} {ZEN_SYMBOL} sent successfully {CHECK_MARK}")
        return True

    except Exception as e:
        print(Fore.RED + f"Failed to send native token: {str(e)} {CROSS_MARK}")
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

def print_header():
    print(Fore.YELLOW + "\n" + "="*70)
    print(Fore.CYAN + "🚀 Web3 Token Manager - ZenChain Edition")
    print(Fore.YELLOW + "="*70)

def print_task_separator():
    print(Fore.YELLOW + "\n" + "-"*50)

def main():
    try:
        print_header()
        
        if not check_connection():
            return

        accounts = load_accounts()
        if not accounts:
            print(Fore.RED + "\n❌ No accounts found in .env file")
            return

        print(Fore.GREEN + f"\n✨ Loaded {len(accounts)} accounts")
        token_manager = TokenManager(web3)

        # Deploy initial contracts
        initial_account = accounts[0]
        token_manager.deploy_token(initial_account[0], initial_account[1], 1000000)
        token_manager.deploy_nft(initial_account[0], initial_account[1])

        while True:
            for account_address, private_key in accounts:
                print(Fore.YELLOW + "\n" + "="*70)
                print(Fore.CYAN + f"📍 Processing Account: {account_address}")
                print(Fore.YELLOW + "="*70)

                # Task 1: Show initial balance
                initial_balance = get_balance(account_address)
                print_balance_info(account_address, initial_balance, "Initial")

                # Task 2: Send native token to random address
                send_native_token(account_address, private_key)

                # Task 3: Deploy storage contract
                deploy_storage_contract(account_address, private_key)

                # Generate random address for token/NFT operations
                random_receiver = web3.eth.account.create()

                # Task 6: Send tokens
                token_manager.send_token(account_address, private_key, random_receiver.address, 100)

                # Task 7: Send NFT
                token_id = token_manager.mint_nft(account_address, private_key, "ipfs://example")
                if token_id is not None:
                    token_manager.send_nft(account_address, private_key, random_receiver.address, token_id)

                # Task 8: Burn tokens
                token_manager.burn_token(account_address, private_key, 10)

                # Task 9: Burn NFT
                if token_id is not None:
                    token_manager.burn_nft(account_address, private_key, token_id)

                # Task 10: Mint new tokens
                token_manager.mint_token(account_address, private_key, 500)

                # Task 11: Mint new NFT
                token_manager.mint_nft(account_address, private_key, "ipfs://example2")

                # Show final balance
                final_balance = get_balance(account_address)
                print_balance_info(account_address, final_balance, "Final")

                print_task_separator()
                time.sleep(10)  # Delay between accounts

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n🔴 Program stopped by user")
    except Exception as e:
        print(Fore.RED + f"\n❌ An error occurred: {str(e)}")

if __name__ == "__main__":
    main()