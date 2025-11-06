from solcx import compile_standard, install_solc
import json, os

install_solc("0.8.0")

with open("contracts/IDVault.sol", "r") as file:
    contract_source = file.read()

compiled_sol = compile_standard({
    "language": "Solidity",
    "sources": {"IDVault.sol": {"content": contract_source}},
    "settings": {
        "outputSelection": {"*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}}
    },
}, solc_version="0.8.0")

with open("compiled.json", "w") as f:
    json.dump(compiled_sol, f)

print("✅ Contract compiled successfully! Output saved to compiled.json")
