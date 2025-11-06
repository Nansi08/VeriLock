from web3 import Web3
import json

# Connect to Ganache
ganache_url = "http://127.0.0.1:8545"
web3 = Web3(Web3.HTTPProvider(ganache_url))
web3.eth.default_account = web3.eth.accounts[0]

# Load compiled contract
with open("build/contracts/IDVault.json") as f:
    contract_json = json.load(f)
    contract_abi = contract_json["abi"]

# Use your deployed contract address
contract_address = "0x4309A738D26DA264c397F277C0b5F033AD4b9Aa7"
contract = web3.eth.contract(address=contract_address, abi=contract_abi)

# Save to a file for Flask to use
data = {
    "contract_address": contract_address,
    "abi": contract_abi
}

with open("contract_data.json", "w") as outfile:
    json.dump(data, outfile, indent=2)

print("✅ Contract deployed successfully!")
print(f"Address: {contract_address}")
