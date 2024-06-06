from fastapi import FastAPI, HTTPException
from web3 import Web3
from pydantic import BaseModel
from typing import List
from ERC20 import erc20_abi
from web3.middleware import geth_poa_middleware
from config import INFURA_ID
app = FastAPI()

# Подключение к сети Polygon через Infura
infura_id = INFURA_ID
infura_url = f'https://polygon-mainnet.infura.io/v3/{infura_id}'
web3 = Web3(Web3.HTTPProvider(infura_url))

# Добавление middleware для работы с POA
web3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Проверка подключения
if not web3.is_connected():
    raise ConnectionError("Failed to connect to Polygon")

# Адрес контракта токена
token_address = '0x1a9b54a3075119f1546c52ca0940551a6ce5d2d0'
checksum_token_address = web3.to_checksum_address(token_address)

# Создание контракта
token_contract = web3.eth.contract(address=checksum_token_address, abi=erc20_abi)

class AddressList(BaseModel):
    addresses: List[str]


# Функция для получения списка топ N адресов с наибольшими балансами
def fetch_top_addresses(n: int) -> List[tuple]:
    try:
        # Список известных адресов
        known_addresses = [
            "0x0000000000000000000000000000000000000000", #ETH
            "0xdAC17F958D2ee523a2206206994597C13D831ec7", #USDT
            "0xB8c77482e45F1F44dE1745F52C74426C631bDD52", #BNB
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", #USDC
            "0x514910771AF9Ca656af840dff83E8264EcF986CA", #LINK
            "0x6B175474E89094C44Da98b954EedeAC495271d0F", #DAI
            "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984", #UNI
            "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599", #WBTC
            "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"  #AAVEs
        ]

        # Получение баланса для каждого известного адреса
        top_balances = []
        for address in known_addresses:
            balance = token_contract.functions.balanceOf(address).call()
            top_balances.append((address, balance))

        # Сортировка списка по балансам в порядке убывания
        top_balances.sort(key=lambda x: x[1], reverse=True)

        # Выбор топ N адресов с наибольшими балансами
        top_N_addresses = top_balances[:n]

        return top_N_addresses
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_top/{n}")
def get_top(n: int):
    try:
        top_addresses = fetch_top_addresses(n)
        return top_addresses
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/get_balance_batch")
def get_balance_batch(address_list: AddressList):
    try:
        balances = []
        for address in address_list.addresses:
            checksum_address = web3.to_checksum_address(address)
            balance = token_contract.functions.balanceOf(checksum_address).call()
            balance_in_ether = web3.from_wei(balance, 'ether')
            balances.append({
                "address": address,
                "balance": str(balance_in_ether),
                "balance_in_wei": balance
            })
        return balances
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get_balance/{address}")
def get_balance(address: str):
    try:
        checksum_address = web3.to_checksum_address(address)
        balance = token_contract.functions.balanceOf(checksum_address).call()
        token_symbol = token_contract.functions.symbol().call()
        balance_in_ether = web3.from_wei(balance, 'ether')
        return {
            "balance": str(balance_in_ether),
            "balance_in_wei": balance,
            "token_symbol": token_symbol
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get_token_info/{token_address}")
def get_token_info(token_address: str):
    try:
        # Преобразование непроверенного адреса в проверенный
        checksum_token_address = Web3.to_checksum_address(token_address)

        # Создание контракта для данного адреса
        token_contract = web3.eth.contract(address=checksum_token_address, abi=erc20_abi)

        # Получение информации о токене
        symbol = token_contract.functions.symbol().call()
        name = token_contract.functions.name().call()
        total_supply = token_contract.functions.totalSupply().call()

        return {
            "symbol": symbol,
            "name": name,
            "total_supply": total_supply
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
