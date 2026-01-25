from web3 import Web3
from web3.middleware import geth_poa_middleware
from typing import Optional, Dict, Any
import json
import logging
from pathlib import Path
from app.core.config import settings

logger = logging.getLogger(__name__)

class Web3Client:
    _instance: Optional['Web3Client'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.w3: Optional[Web3] = None
        self.network_config: Optional[Dict[str, Any]] = None
        self._initialized = True
        self._load_network_config()
        self._connect()
    
    def _load_network_config(self):
        try:
            config_path = Path(__file__).parent.parent.parent / "contracts.json"
            if not config_path.exists():
                logger.warning(f"contracts.json not found at {config_path}")
                return
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            network = settings.BLOCKCHAIN_NETWORK or "arbitrum-sepolia"
            if network not in config["networks"]:
                logger.error(f"Network {network} not found in contracts.json")
                return
            self.network_config = config["networks"][network]
            logger.info(f"📋 Loaded config for {self.network_config['name']}")
        except Exception as e:
            logger.error(f"Error loading network config: {e}", exc_info=True)
    
    def _connect(self):
        if not self.network_config:
            logger.error("No network configuration available")
            return
        try:
            rpc_url = self.network_config["rpc"]
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))

            if self.network_config.get("testnet"):
                self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            if self.w3.is_connected():
                logger.info(f"✅ Connected to {self.network_config['name']}")
                logger.info(f"📡 Latest block: {self.w3.eth.block_number}")
            else:
                logger.error(f"❌ Failed to connect to {self.network_config['name']}")
        except Exception as e:
            logger.error(f"Error connecting to blockchain: {e}", exc_info=True)
    
    def is_connected(self) -> bool:
        return self.w3 is not None and self.w3.is_connected()
    
    def get_contract_address(self, contract_name: str) -> Optional[str]:
        if not self.network_config:
            return None
        
        contracts = self.network_config.get("contracts", {})
        address = contracts.get(contract_name)
        if address and address != "0x0000000000000000000000000000000000000000":
            return address
        return None
    
    def get_latest_block(self) -> int:
        if not self.is_connected():
            return 0
        return self.w3.eth.block_number
    
    def get_block(self, block_number: int) -> Optional[Dict]:
        if not self.is_connected():
            return None
        try:
            return dict(self.w3.eth.get_block(block_number))
        except Exception as e:
            logger.error(f"Error getting block {block_number}: {e}")
            return None
    
    def get_transaction(self, tx_hash: str) -> Optional[Dict]:
        if not self.is_connected():
            return None
        try:
            return dict(self.w3.eth.get_transaction(tx_hash))
        except Exception as e:
            logger.error(f"Error getting transaction {tx_hash}: {e}")
            return None
    
    def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict]:
        if not self.is_connected():
            return None
        try:
            return dict(self.w3.eth.get_transaction_receipt(tx_hash))
        except Exception as e:
            logger.error(f"Error getting receipt {tx_hash}: {e}")
            return None

web3_client = Web3Client()
