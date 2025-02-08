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

codigo_operado = "IOTAUSDT"
ativo_operado = "USDT"
periodo_candle = Client.KLINE_INTERVAL_1MINUTE
quantidade = 20

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

def pegando_dados(codigo, intervalo):
    candles = cliente_binance.get_klines(symbol=codigo, interval=intervalo, limit=1000)
    precos = pd.DataFrame(candles)
    precos.columns = ["tempo_abertura", "abertura", "maxima", "minima", "fechamento", "volume", "tempo_fechamento", "moedas_negociadas", "numero_trades",
                        "volume_ativo_base_compra", "volume_ativo_cotação", "-"]
    precos = precos[["fechamento", "tempo_fechamento"]]
    precos["tempo_fechamento"] = pd.to_datetime(precos["tempo_fechamento"], unit="ms").dt.tz_localize("UTC")
    precos["tempo_fechamento"] = precos["tempo_fechamento"].dt.tz_convert("America/Sao_Paulo")

    return precos

def estrategia_trade(dados, codigo_ativo, ativo_operado, quantidade, posicao):
    dados["media_rapida"] = dados["fechamento"].rolling(window=7).mean()
    dados["media_devagar"] = dados["fechamento"].rolling(window=40).mean()

    ultima_media_rapida = dados["media_rapida"].iloc[-1]
    ultima_media_devagar = dados["media_devagar"].iloc[-1]

    print(f"Última Média Rápida: {ultima_media_rapida} | Última Média Devagar: {ultima_media_devagar}")
    mostrar_saldo()

    conta = cliente_binance.get_account()

    for ativo in conta["balances"]:
        if ativo["asset"] == ativo_operado:
            quantidade_atual = float(ativo["free"])

    if ultima_media_rapida > ultima_media_devagar and not posicao:
        quantidade_ajustada = ajustar_quantidade(quantidade, min_qty, max_qty, step_size)
        order = cliente_binance.create_order(
            symbol=codigo_ativo,
            side=SIDE_BUY,
            type=ORDER_TYPE_MARKET,
            quantity=quantidade_ajustada
        )
        print("COMPROU O ATIVO")
        mostrar_saldo()
        posicao = True

    elif ultima_media_rapida < ultima_media_devagar and posicao:
        quantidade_ajustada = ajustar_quantidade(quantidade_atual, min_qty, max_qty, step_size)
        order = cliente_binance.create_order(
            symbol=codigo_ativo,
            side=SIDE_SELL,
            type=ORDER_TYPE_MARKET,
            quantity=quantidade_ajustada
        )
        print("VENDEU O ATIVO")
        mostrar_saldo()
        posicao = False

    return posicao

posicao_atual = False

while True:
    try:
        dados_atualizados = pegando_dados(codigo=codigo_operado, intervalo=periodo_candle)
        posicao_atual = estrategia_trade(dados_atualizados, codigo_ativo=codigo_operado,
                                            ativo_operado=ativo_operado, quantidade=quantidade, posicao=posicao_atual)
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

    time.sleep(60)
