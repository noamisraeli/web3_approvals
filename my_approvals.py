# What approval?
# approval/approve is a core concept in the interface of ERC20 token based contracts
# The main purpose of the approval/approve concept is to let identities in the blockchain to get partial ownership capabilities over other identities' tokens.
# when identity X approves identity Y for Z amount of tokens, the outcome of this action gives Y the ability to transfer actions on behaf of X over the Z amount of tokens.
# Unlike a regular transfer transaction, which can be done only by the identity holding the tokens, the transferFrom transaction can be done by any identity who got approved by the identity holding the tokens.
# Another difference is that the transferFrom has an additional limitation on what it can do and don't and it is the approved amount:
# A regular transfer is based on recording a balance book of all participants in the token's trading game, while transferFrom is additionally based on the permited amount of tokens that can be traded based on a single approve.
# if A approves B with an amount of 1 token, the transferFrom action B can do is limitted to 1 token.

import sys
import logging
import typing
import json
import sha3

import pydantic

import typer

from web3 import Web3
from ens import ENS

from web3.middleware import geth_poa_middleware 
from eth_abi.codec import ABICodec
from web3._utils.events import get_event_data

_logger = logging.getLogger(__name__)
_logger.addHandler(logging.StreamHandler(sys.stdout))
 
E20_APPROVAL_ABI_JSON = """{
        "anonymous": false,
        "inputs": [
            {
                "indexed": true,
                "name": "owner",
                "type": "address"
            },
            {
                "indexed": true,
                "name": "spender",
                "type": "address"
            },
            {
                "indexed": false,
                "name": "value",
                "type": "uint256"
            }
        ],
        "name": "Approval",
        "type": "event"
}"""

API_KEY = "7e135dbc63904c30808f84ff52a92343"

BASE_URL = f"https://mainnet.infura.io/v3/{API_KEY}"

ADDRESS_TO_NAME_MAPPING = {
    '0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45': 'Uniswap V3: Router 2',
    '0x9fa69536d1cda4A04cFB50688294de75B505a9aE': 'DeRace: DERC Token',
    '0x9AAb3f75489902f3a48495025729a0AF77d4b11e': 'Kyber: Deployer 3',
    '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D': 'Uniswap V2: Router 2',
    '0x3dfd23A6c5E8BbcFc9581d2E864a68feb6a076d3': 'Aave: Lending Pool Core V1',
    '0x5e3Ef299fDDf15eAa0432E6e66473ace8c13D908': 'Polygon (Matic): PoS Staking Contract',
    '0x111111125434b319222CdBf8C261674aDB56F3ae': '1inch v2: Aggregation Router',
    '0xECf0bdB7B3F349AbfD68C3563678124c5e8aaea3': 'Kyber: Staking'
}


class ABIParam(pydantic.BaseModel):
    indexed: bool
    name: str
    type: str


class EventABI(pydantic.BaseModel):
    inputs: typing.List[ABIParam]
    name: str
    type = 'event'

    @property
    def signature_string(self) -> str:
        params_string = ",".join(param.type for param in self.inputs)
        return f"{self.name}({params_string})"

    @property
    def signature_hex(self) -> str:
        k = sha3.keccak_256()

        k.update(self.signature_string.encode())
        return "0x" + k.hexdigest() 


def get_address_as_topic(address: str):
    return '0x000000000000000000000000' + address[-40:]

def get_name_from_address(ns: ENS, address: str):
    name = ns.name(address) # not working for some reason

    if name is None:
        return ADDRESS_TO_NAME_MAPPING.get(address) or address
    else:
        return name


def main(
    account_address: str = typer.Option(..., '--address'), 
    url: typing.Optional[str] = typer.Option(None, '--eth-node-api'),
    verbose: bool = typer.Option(False, '--verbose')
    ):
    base_url = url or BASE_URL
    if verbose:
        _logger.setLevel(logging.DEBUG)
    else:
        _logger.setLevel(logging.INFO)
    
    abi_as_dict = json.loads(E20_APPROVAL_ABI_JSON)

    abi = EventABI.parse_obj(abi_as_dict)
    
    provider = Web3.HTTPProvider(base_url)
    w3 = Web3(provider)

    name_resolving = ENS.fromWeb3(w3)

    # for compatibility of the POA api
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    filter_by_approve_event = w3.eth.filter(
        dict(
            topics=[
            abi.signature_hex, 
            get_address_as_topic(account_address)
            ], 
            fromBlock=0
        )
    )

    codec: ABICodec = w3.codec

    all_events = filter_by_approve_event.get_all_entries()

    if len(all_events) is None:
        _logger.info("There are no approvals related to this address")
    else:
        for event in all_events:
            # Using an internal function for parsing the entries result
            event_args = get_event_data(codec, event_abi=abi_as_dict, log_entry=event)['args']

            spender_name = get_name_from_address(name_resolving, event_args['spender'])
            value_approved = event_args['value']

            _logger.info( f"Approval on {spender_name} on amount of {value_approved}")

            transaction_id =  event['transactionHash']
            log_index = event['logIndex']
            _logger.debug(f"transaction id: {transaction_id.hex()} " \
                          f"log_index: {log_index}")


if __name__ == '__main__':
    typer.run(main)
