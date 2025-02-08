import pandas as pd
import os 
import time 
from binance.client import Client
from binance.enums import *
import requests
from binance.exceptions import BinanceAPIException, BinanceRequestException
from requests.exceptions import ConnectionError, Timeout
from urllib3.exceptions import ProtocolError

from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("KEY_BINANCE")
secret_key = os.getenv("SECRET_BINANCE")

cliente_binance = Client(api_key, secret_key, {"timeout": 30})

def obter_filtro_lot_size(codigo_ativo):
    symbol_info = cliente_binance.get_symbol_info(codigo_ativo)
    lot_size_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')
    return float(lot_size_filter['minQty']), float(lot_size_filter['maxQty']), float(lot_size_filter['stepSize'])

def ajustar_quantidade(quantidade, min_qty, max_qty, step_size):
    quantidade = max(min_qty, min(quantidade, max_qty))  # Garantir que está dentro do intervalo
    return round(quantidade // step_size * step_size, len(str(step_size).split('.')[1]))

def calcular_quantidade_usando_valor(codigo_ativo, valor_usd):
    ticker = cliente_binance.get_ticker(symbol=codigo_ativo)
    preco_atual = float(ticker['lastPrice'])
    quantidade = valor_usd / preco_atual
    return quantidade

codigo_operado = "IOTAUSDT"
ativo_operado = "IOTA"
valor_compra = 10.0  # Valor em dólares para cada compra
intervalo_compras = 500  # Intervalo entre compras em segundos (5 minutos)

# Obter os limites do filtro LOT_SIZE
min_qty, max_qty, step_size = obter_filtro_lot_size(codigo_operado)

def mostrar_saldo():
    try:
        conta = cliente_binance.get_account()
        print("Saldo atual:")
        for ativo in conta["balances"]:
            if float(ativo["free"]) > 0:
                print(f"Ativo: {ativo['asset']} | Quantidade: {ativo['free']}")
    except Exception as e:
        print(f"Erro ao obter saldo: {e}")

def realizar_compra(codigo_ativo, valor_usd):
    try:
        quantidade = calcular_quantidade_usando_valor(codigo_ativo, valor_usd)
        quantidade_ajustada = ajustar_quantidade(quantidade, min_qty, max_qty, step_size)
        order = cliente_binance.create_order(
            symbol=codigo_ativo,
            side=SIDE_BUY,
            type=ORDER_TYPE_MARKET,
            quantity=quantidade_ajustada
        )
        print("COMPROU O ATIVO")
        mostrar_saldo()
    except BinanceAPIException as e:
        print(f"Erro na API da Binance: {e}")
    except BinanceRequestException as e:
        print(f"Erro de requisição: {e}")
    except ConnectionError as e:
        print(f"Erro de conexão: {e}")
    except Timeout as e:
        print(f"Timeout na conexão: {e}")
    except ProtocolError as e:
        print(f"Erro de protocolo: {e}")
    except Exception as e:
        print(f"Erro inesperado: {e}")

while True:
    try:
        realizar_compra(codigo_operado, valor_compra)
    except Exception as e:
        print(f"Erro durante a execução: {e}")

    print(f"Aguardando {intervalo_compras} segundos para a próxima compra...")
    time.sleep(intervalo_compras)
