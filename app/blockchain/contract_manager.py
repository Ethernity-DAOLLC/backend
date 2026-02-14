from web3 import Web3
from web3.contract import Contract
from typing import Optional, Dict, Any, List
import json
from pathlib import Path
import logging

from .web3_client import web3_client

logger = logging.getLogger(__name__)

class ContractManager:
    def __init__(self):
        self.contracts: Dict[str, Contract] = {}
        self.abis: Dict[str, List] = {}
        self._load_abis()
    
    def _load_abis(self):
        self.abis["token"] = [
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "sender", "type": "address"},
                    {"indexed": True, "name": "receiver", "type": "address"},
                    {"indexed": False, "name": "value", "type": "uint256"}
                ],
                "name": "Transfer",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "account", "type": "address"},
                    {"indexed": False, "name": "amount", "type": "uint256"},
                    {"indexed": False, "name": "totalBurns", "type": "uint256"},
                    {"indexed": False, "name": "timestamp", "type": "uint256"}
                ],
                "name": "TokensBurned",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "account", "type": "address"},
                    {"indexed": False, "name": "amount", "type": "uint256"},
                    {"indexed": False, "name": "totalRenews", "type": "uint256"},
                    {"indexed": False, "name": "timestamp", "type": "uint256"}
                ],
                "name": "TokensRenewed",
                "type": "event"
            }
        ]

        self.abis["factory"] = [
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "fundAddress", "type": "address"},
                    {"indexed": True, "name": "owner", "type": "address"},
                    {"indexed": False, "name": "initialDeposit", "type": "uint256"},
                    {"indexed": False, "name": "timestamp", "type": "uint256"}
                ],
                "name": "FundCreated",
                "type": "event"
            }
        ]

        self.abis["governance"] = [
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "proposalId", "type": "uint256"},
                    {"indexed": True, "name": "proposer", "type": "address"},
                    {"indexed": False, "name": "title", "type": "string"},
                    {"indexed": False, "name": "proposalType", "type": "uint8"}
                ],
                "name": "ProposalCreated",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "proposalId", "type": "uint256"},
                    {"indexed": True, "name": "voter", "type": "address"},
                    {"indexed": False, "name": "support", "type": "bool"},
                    {"indexed": False, "name": "votingPower", "type": "uint256"}
                ],
                "name": "VoteCast",
                "type": "event"
            }
        ]

        self.abis["fund"] = [
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "owner", "type": "address"},
                    {"indexed": False, "name": "grossAmount", "type": "uint256"},
                    {"indexed": False, "name": "feeAmount", "type": "uint256"},
                    {"indexed": False, "name": "netToFund", "type": "uint256"}
                ],
                "name": "Deposited",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "owner", "type": "address"},
                    {"indexed": False, "name": "totalBalance", "type": "uint256"}
                ],
                "name": "RetirementStarted",
                "type": "event"
            }
        ]
        logger.info("📚 Contract ABIs loaded")
    
    def get_contract(self, contract_name: str) -> Optional[Contract]:
        if contract_name in self.contracts:
            return self.contracts[contract_name]
        address = web3_client.get_contract_address(contract_name)
        if not address:
            logger.warning(f"No address found for {contract_name}")
            return None
        if not web3_client.is_connected():
            logger.error("Web3 not connected")
            return None
        abi = self.abis.get(contract_name, [])
        if not abi:
            logger.warning(f"No ABI found for {contract_name}")
            return None
        try:
            contract = web3_client.w3.eth.contract(
                address=Web3.to_checksum_address(address),
                abi=abi
            )
            self.contracts[contract_name] = contract
            logger.info(f"✅ Contract loaded: {contract_name} at {address}")
            return contract
            
        except Exception as e:
            logger.error(f"Error loading contract {contract_name}: {e}")
            return None
    
    def parse_event_log(self, contract_name: str, log: Dict) -> Optional[Dict]:
        contract = self.get_contract(contract_name)
        if not contract:
            return None
        
        try:
            for event_abi in contract.events:
                try:
                    event = contract.events[event_abi]
                    parsed = event.process_log(log)
                    return {
                        "event_name": parsed["event"],
                        "args": dict(parsed["args"]),
                        "transaction_hash": parsed["transactionHash"].hex(),
                        "block_number": parsed["blockNumber"],
                        "log_index": parsed["logIndex"]
                    }
                except:
                    continue
            return None
            
        except Exception as e:
            logger.error(f"Error parsing event log: {e}")
            return None

contract_manager = ContractManager()
