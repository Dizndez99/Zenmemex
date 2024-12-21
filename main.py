from web3 import Web3
import time
import os
import secrets
import random
from eth_account import Account
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
install_solc('0.8.19')
set_solc_version('0.8.19')

# Blockchain Configuration
RPC_URL = os.getenv('RPC_URL', "https://zenchain-testnet.api.onfinality.io/public")
CHAIN_ID = 8408
web3 = Web3(Web3.HTTPProvider(RPC_URL))

# Smart Contract Sources
SIMPLE_STORAGE_SOURCE = '''
pragma solidity ^0.8.19;

contract SimpleStorage {
    uint256 private storedData;
    address public owner;

    constructor() {
        storedData = 100;
        owner = msg.sender;
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
pragma solidity ^0.8.19;

contract DezToken {
    string public name;
    string public symbol;
    uint8 public decimals = 18;
    uint256 public totalSupply;
    address public owner;
    
    mapping(address => uint256) private balances;
    
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Burn(address indexed from, uint256 value);
    event Mint(address indexed to, uint256 value);

    constructor(string memory _name, string memory _symbol, uint256 initialSupply) {
        name = _name;
        symbol = _symbol;
        owner = msg.sender;
        _mint(msg.sender, initialSupply * 10**uint256(decimals));
    }
    
    function balanceOf(address account) public view returns (uint256) {
        return balances[account];
    }
    
    function transfer(address to, uint256 amount) public returns (bool) {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        balances[to] += amount;
        emit Transfer(msg.sender, to, amount);
        return true;
    }
    
    function burn(uint256 amount) public returns (bool) {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        totalSupply -= amount;
        emit Burn(msg.sender, amount);
        return true;
    }
    
    function mint(address to, uint256 amount) public returns (bool) {
        require(msg.sender == owner, "Only owner can mint");
        _mint(to, amount);
        return true;
    }
    
    function _mint(address account, uint256 amount) internal {
        totalSupply += amount;
        balances[account] += amount;
        emit Mint(account, amount);
    }
}
'''

class TokenManager:
    def __init__(self, web3):
        self.web3 = web3
        self.token_contract = None
        self.token_address = None
        self.random_suffix = ''.join(random.choices('0123456789ABCDEF', k=4))

    def deploy_token(self, account_address, private_key):
        try:
            compiled_sol = compile_source(TOKEN_CONTRACT_SOURCE)
            contract_interface = compiled_sol['<stdin>:DezToken']
            
            token_name = f"Dez {self.random_suffix}"
            token_symbol = f"DEZ{self.random_suffix}"
            initial_supply = 1000

            DezToken = self.web3.eth.contract(
                abi=contract_interface['abi'],
                bytecode=contract_interface['bin']
            )

            transaction = DezToken.constructor(token_name, token_symbol, initial_supply).build_transaction({
                'from': account_address,
                'nonce': self.web3.eth.get_transaction_count(account_address),
                'gas': 3000000,
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

            print(Fore.GREEN + f"Token {token_name} ({token_symbol}) deployed at {self.token_address} {CHECK_MARK}")
            return True

        except Exception as e:
            print(Fore.RED + f"Failed to deploy token: {str(e)} {CROSS_MARK}")
            return False

    def transfer_random_amount(self, from_address, private_key, to_address):
        try:
            balance = self.token_contract.functions.balanceOf(from_address).call()
            if balance == 0:
                print(Fore.YELLOW + "No tokens available to transfer")
                return False

            random_amount = random.randint(1, min(balance, 100 * 10**18))
            
            transaction = self.token_contract.functions.transfer(
                to_address,
                random_amount
            ).build_transaction({
                'from': from_address,
                'nonce': self.web3.eth.get_transaction_count(from_address),
                'gas': 200000,
                'gasPrice': self.web3.eth.gas_price
            })

            signed_tx = self.web3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            self.web3.eth.wait_for_transaction_receipt(tx_hash)

            print(Fore.GREEN + f"Random amount of tokens transferred to {to_address} {CHECK_MARK}")
            return True

        except Exception as e:
            print(Fore.RED + f"Failed to transfer tokens: {str(e)} {CROSS_MARK}")
            return False

    def burn_random_amount(self, from_address, private_key):
        try:
            balance = self.token_contract.functions.balanceOf(from_address).call()
            if balance == 0:
                print(Fore.YELLOW + "No tokens available to burn")
                return False

            random_amount = random.randint(1, min(balance, 50 * 10**18))
            
            transaction = self.token_contract.functions.burn(
                random_amount
            ).build_transaction({
                'from': from_address,
                'nonce': self.web3.eth.get_transaction_count(from_address),
                'gas': 200000,
                'gasPrice': self.web3.eth.gas_price
            })

            signed_tx = self.web3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            self.web3.eth.wait_for_transaction_receipt(tx_hash)

            print(Fore.GREEN + f"Random amount of tokens burned {CHECK_MARK}")
            return True

        except Exception as e:
            print(Fore.RED + f"Failed to burn tokens: {str(e)} {CROSS_MARK}")
            return False

    def mint_random_amount(self, owner_address, private_key, to_address):
        try:
            random_amount = random.randint(1, 100) * 10**18
            
            transaction = self.token_contract.functions.mint(
                to_address,
                random_amount
            ).build_transaction({
                'from': owner_address,
                'nonce': self.web3.eth.get_transaction_count(owner_address),
                'gas': 200000,
                'gasPrice': self.web3.eth.gas_price
            })

            signed_tx = self.web3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            self.web3.eth.wait_for_transaction_receipt(tx_hash)

            print(Fore.GREEN + f"Random amount of tokens minted to {to_address} {CHECK_MARK}")
            return True

        except Exception as e:
            print(Fore.RED + f"Failed to mint tokens: {str(e)} {CROSS_MARK}")
            return False
            # Part 2: NFT functionality and main execution logic

NFT_CONTRACT_SOURCE = '''
pragma solidity ^0.8.19;

contract DezNFT {
    string public name;
    string public symbol;
    address public owner;
    
    struct NFT {
        uint256 id;
        address owner;
        bool exists;
    }
    
    mapping(uint256 => NFT) public nfts;
    mapping(address => uint256) public balances;
    uint256 public totalSupply;
    uint256 public maxSupply;
    
    event Transfer(address indexed from, address indexed to, uint256 tokenId);
    event Mint(address indexed to, uint256 tokenId);
    event Burn(address indexed from, uint256 tokenId);
    
    constructor(string memory _name, string memory _symbol, uint256 _maxSupply) {
        name = _name;
        symbol = _symbol;
        maxSupply = _maxSupply;
        owner = msg.sender;
    }
    
    function mint(address to) public returns (uint256) {
        require(msg.sender == owner, "Only owner can mint");
        require(totalSupply < maxSupply, "Max supply reached");
        
        totalSupply++;
        uint256 tokenId = totalSupply;
        
        nfts[tokenId] = NFT(tokenId, to, true);
        balances[to]++;
        
        emit Mint(to, tokenId);
        return tokenId;
    }
    
    function burn(uint256 tokenId) public {
        require(nfts[tokenId].exists, "Token does not exist");
        require(nfts[tokenId].owner == msg.sender, "Not token owner");
        
        delete nfts[tokenId];
        balances[msg.sender]--;
        totalSupply--;
        
        emit Burn(msg.sender, tokenId);
    }
    
    function transfer(address to, uint256 tokenId) public {
        require(nfts[tokenId].exists, "Token does not exist");
        require(nfts[tokenId].owner == msg.sender, "Not token owner");
        
        nfts[tokenId].owner = to;
        balances[msg.sender]--;
        balances[to]++;
        
        emit Transfer(msg.sender, to, tokenId);
    }
    
    function balanceOf(address account) public view returns (uint256) {
        return balances[account];
    }
    
    function ownerOf(uint256 tokenId) public view returns (address) {
        require(nfts[tokenId].exists, "Token does not exist");
        return nfts[tokenId].owner;
    }
}
'''

class NFTManager:
    def __init__(self, web3):
        self.web3 = web3
        self.nft_contract = None
        self.nft_address = None
        self.random_suffix = ''.join(random.choices('0123456789ABCDEF', k=4))
        self.owned_tokens = {}  # Track owned tokens for each address

    def deploy_nft(self, account_address, private_key):
        try:
            compiled_sol = compile_source(NFT_CONTRACT_SOURCE)
            contract_interface = compiled_sol['<stdin>:DezNFT']
            
            nft_name = f"Dez NFT {self.random_suffix}"
            nft_symbol = f"DNFT{self.random_suffix}"
            max_supply = 1000

            DezNFT = self.web3.eth.contract(
                abi=contract_interface['abi'],
                bytecode=contract_interface['bin']
            )

            transaction = DezNFT.constructor(nft_name, nft_symbol, max_supply).build_transaction({
                'from': account_address,
                'nonce': self.web3.eth.get_transaction_count(account_address),
                'gas': 3000000,
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

            print(Fore.GREEN + f"NFT Collection {nft_name} ({nft_symbol}) deployed at {self.nft_address} {CHECK_MARK}")
            return True

        except Exception as e:
            print(Fore.RED + f"Failed to deploy NFT collection: {str(e)} {CROSS_MARK}")
            return False

    def mint_random_nfts(self, owner_address, private_key, to_address):
        try:
            current_supply = self.nft_contract.functions.totalSupply().call()
            max_supply = self.nft_contract.functions.maxSupply().call()
            
            if current_supply >= max_supply:
                print(Fore.YELLOW + "Maximum supply reached")
                return False

            mint_count = random.randint(1, min(5, max_supply - current_supply))
            minted_tokens = []

            for _ in range(mint_count):
                transaction = self.nft_contract.functions.mint(
                    to_address
                ).build_transaction({
                    'from': owner_address,
                    'nonce': self.web3.eth.get_transaction_count(owner_address),
                    'gas': 200000,
                    'gasPrice': self.web3.eth.gas_price
                })

                signed_tx = self.web3.eth.account.sign_transaction(transaction, private_key)
                tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
                
                # Track minted token
                token_id = current_supply + len(minted_tokens) + 1
                minted_tokens.append(token_id)
                if to_address not in self.owned_tokens:
                    self.owned_tokens[to_address] = []
                self.owned_tokens[to_address].append(token_id)

            print(Fore.GREEN + f"Minted {mint_count} NFTs to {to_address} {CHECK_MARK}")
            return True

        except Exception as e:
            print(Fore.RED + f"Failed to mint NFTs: {str(e)} {CROSS_MARK}")
            return False

    def transfer_random_nfts(self, from_address, private_key, to_address):
        try:
            if from_address not in self.owned_tokens or not self.owned_tokens[from_address]:
                print(Fore.YELLOW + "No NFTs available to transfer")
                return False

            transfer_count = random.randint(1, min(3, len(self.owned_tokens[from_address])))
            tokens_to_transfer = random.sample(self.owned_tokens[from_address], transfer_count)

            for token_id in tokens_to_transfer:
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

                # Update tracking
                self.owned_tokens[from_address].remove(token_id)
                if to_address not in self.owned_tokens:
                    self.owned_tokens[to_address] = []
                self.owned_tokens[to_address].append(token_id)

            print(Fore.GREEN + f"Transferred {transfer_count} NFTs to {to_address} {CHECK_MARK}")
            return True

        except Exception as e:
            print(Fore.RED + f"Failed to transfer NFTs: {str(e)} {CROSS_MARK}")
            return False

    def burn_random_nfts(self, from_address, private_key):
        try:
            if from_address not in self.owned_tokens or not self.owned_tokens[from_address]:
                print(Fore.YELLOW + "No NFTs available to burn")
                return False

            burn_count = random.randint(1, min(2, len(self.owned_tokens[from_address])))
            tokens_to_burn = random.sample(self.owned_tokens[from_address], burn_count)

            for token_id in tokens_to_burn:
                transaction = self.nft_contract.functions.burn(
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

                # Update tracking
                self.owned_tokens[from_address].remove(token_id)

            print(Fore.GREEN + f"Burned {burn_count} NFTs {CHECK_MARK}")
            return True

        except Exception as e:
            print(Fore.RED + f"Failed to burn NFTs: {str(e)} {CROSS_MARK}")
            return False

def deploy_storage_contract(web3, account_address, private_key):
    try:
        compiled_sol = compile_source(SIMPLE_STORAGE_SOURCE)
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

        print(Fore.GREEN + f"Storage Contract deployed at {tx_receipt.contractAddress} {CHECK_MARK}")
        return tx_receipt.contractAddress

    except Exception as e:
        print(Fore.RED + f"Failed to deploy storage contract: {str(e)} {CROSS_MARK}")
        return None

def send_native_token(web3, sender_address, private_key, receiver_address, amount):
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

        print(Fore.GREEN + f"Native token sent to {receiver_address} {CHECK_MARK}")
        return True

    except Exception as e:
        print(Fore.RED + f"Failed to send native token: {str(e)} {CROSS_MARK}")
        return False

def main():
    try:
        # Initialize managers
        token_manager = TokenManager(web3)
        nft_manager = NFTManager(web3)

        # Load accounts from .env
        accounts = []
        index = 1
        while True:
            address = os.getenv(f'ACCOUNT_ADDRESS_{index}')
            private_key = os.getenv(f'PRIVATE_KEY_{index}')
            if not address or not private_key:
                break
            accounts.append((web3.to_checksum_address(address), private_key))
            index += 1

        if not accounts:
            print(Fore.RED + "No accounts found in .env file")
            return

        # Deploy initial contracts with first account
        print(Fore.CYAN + "\nInitializing contracts...")
        token_manager.deploy_token(accounts[0][0], accounts[0][1])
        nft_manager.deploy_nft(accounts[0][0], accounts[0][1])

        print(Fore.CYAN + "\nStarting main operation loop...")
        while True:
            for sender_address, private_key in accounts:
                try:
                    print("\n" + Fore.YELLOW + "=" * 50)
                    print(Fore.CYAN + f"Processing account: {sender_address}")

                    # Create random receiver address
                    random_receiver = Account.create()
                    
                    # Execute operations
                    operations = [
                        lambda: send_native_token(web3, sender_address, private_key, random_receiver.address, random.uniform(0.00001, 0.0001)),
                        lambda: deploy_storage_contract(web3, sender_address, private_key),
                        lambda: token_manager.transfer_random_amount(sender_address, private_key, random_receiver.address),
                        lambda: nft_manager.transfer_random_nfts(sender_address, private_key, random_receiver.address),
                        lambda: token_manager.burn_random_amount(sender_address, private_key),
                        lambda: nft_manager.burn_random_nfts(sender_address, private_key),
                        lambda: token_manager.mint_random_amount(sender_address, private_key, sender_address),
                        lambda: nft_manager.mint_random_nfts(sender_address, private_key, sender_address)
                    ]

                    # Execute operations in random order
                    random.shuffle(operations)
                    for operation in operations:
                        operation()
                        time.sleep(random.uniform(1, 3))  # Random delay between operations

                    print(Fore.YELLOW + "=" * 50 + "\n")
                    time.sleep(random.uniform(5, 10))  # Random delay between accounts

                except Exception as e:
                    print(Fore.RED + f"Error processing account {sender_address}: {str(e)}")
                    continue

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n🔴 Program stopped by user")
    except Exception as e:
        print(Fore.RED + f"\nCritical error: {str(e)}")

if __name__ == "__main__":
    main()
