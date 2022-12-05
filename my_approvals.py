# What approval?
# approval/approve is a core concept in the interface of ERC20 token based contracts
# The main purpose of the approval/approve concept is to let identities in the blockchain to get partial ownership capabilities over other identities' tokens.
# when identity X approves identity Y for Z amount of tokens, the outcome of this action gives Y the ability to transfer actions on behaf of X over the Z amount of tokens.
# Unlike a regular transfer transaction, which can be done only by the identity holding the tokens, the transferFrom transaction can be done by any identity who got approved by the identity holding the tokens.
# Another difference is that the transferFrom has an additional limitation on what it can do and don't and it is the approved amount:
# A regular transfer is based on recording a balance book of all participants in the token's trading game, while transferFrom is additionally based on the permited amount of tokens that can be traded based on a single approve.
# if A approves B with an amount of 1 token, the transferFrom action B can do is limitted to 1 token.

from web3 import Web3
from ens import ENS

from web3.middleware import geth_poa_middleware 
from eth_abi.codec import ABICodec
from web3._utils.events import get_event_data

APPROVAL_SIGNATUR = 'Approval(address,address,uint256)'

E20_APPROVAL_ABI = {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "name": "owner",
                    "type": "address"
                },
                {
                    "indexed": True,
                    "name": "spender",
                    "type": "address"
                },
                {
                    "indexed": False,
                    "name": "value",
                    "type": "uint256"
                }
            ],
            "name": "Approval",
            "type": "event"
        }

def get_event_signature(signature: str):
    import sha3
    k = sha3.keccak_256()

    k.update(signature.encode())
    return "0x" + k.hexdigest()

def get_address_as_topic(address: str):
    return '0x000000000000000000000000005e20fcf757b55d6e27dea9ba4f90c0b03ef852'

def validate_address(w3: Web3, address: str):
    assert w3.is_address(address)

def get_name_from_address(ns: ENS, address: str):
    MAPPING = {
        '0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45': 'Uniswap V3: Router 2'
    }
    return MAPPING.get(address)

    return ns.name(address) or address

if __name__ == '__main__':
    ACCOUNT_ADDRESS = "0x005e20fCf757B55D6E27dEA9BA4f90C0B03ef852"
    
    API_KEY = "7e135dbc63904c30808f84ff52a92343"

    url = f"https://mainnet.infura.io/v3/{API_KEY}"

    provider = Web3.HTTPProvider(url)

    w3 = Web3(provider)

    name_resolving = ENS.fromWeb3(w3)

    name_resolving.name('0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45')

    # for compatibility of the POA
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    filter_by_approve_event = w3.eth.filter(
        {'topics': [get_event_signature(APPROVAL_SIGNATUR), get_address_as_topic(ACCOUNT_ADDRESS)], 'fromBlock': 0})

    codec: ABICodec = w3.codec

    different_events = set()
    different_spenders = set()
    different_transactions = set()

    for event in filter_by_approve_event.get_all_entries():
        # Using an internal function for parsing the entries result
        event_args = get_event_data(codec, event_abi=E20_APPROVAL_ABI, log_entry=event)['args']

        spender_name = get_name_from_address(name_resolving, event_args['spender'])
        
        message = f"Approval on {spender_name} on amount of {event_args['value']}"
        print(message)

        different_events.add(message)
        different_transactions.add(event['transactionHash'])
        different_spenders.add(spender_name)


    print(f"Total spenders: {different_spenders}")
    print(f"Total transactions: {different_transactions}")