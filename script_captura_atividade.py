# Importação das bibliotecas necessárias
import psutil  # Para coletar informações sobre o sistema (CPU, RAM, discos, etc.)
import pandas as pd  # Para manipular dados e salvar em CSV
from datetime import datetime  # Para trabalhar com datas e horários
import time  # Para fazer pausas no código
import socket  # Para trabalhar com endereços de rede
import os  # Para interagir com o sistema operacional
import logging
# import boto3
# from botocore.exceptions import ClientError
import csv  # Para registrar o tempo dos processos
import requests
from bs4 import BeautifulSoup
from multiprocessing import Process, Queue
# ================================
# Configuração inicial dos arquivos
# ================================
id = 3
timestamp = datetime.now().strftime("%Y-%m-%d")


# Criação do arquivo principal de captura
if not os.path.exists(f"{id}-{timestamp}.csv"):
    df_inicial = pd.DataFrame(columns=[
        'timestamp', 'endereco_mac', 'user', 'cpu', 'ram', 'disco',
        'quantidade_processos', 'bateria', 'temp_cpu', 'temp_bateria'
    ])
    df_inicial.to_csv(f"{id}-{timestamp}.csv", index=False)

# Criação do arquivo de processos
if not os.path.exists(f"{id}_processos_{timestamp}.csv"):
    with open("processos.csv", mode="w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["Timestamp", "Pid", "Nome","Cpu","Ram","Status","TempoVida" ])

# Detecta tipo de família de endereço MAC (compatível Linux/Windows)
AF_LINK = getattr(psutil, "AF_LINK", None) or getattr(socket, "AF_PACKET", None)

# ================================
# Funções auxiliares
# ================================

def formatar_memoria(valor):
    """Converte bytes para MB ou GB formatados."""
    mb = valor / 1024**2
    return f"{mb/1024:.1f} GB" if mb > 1024 else f"{mb:.0f} MB"

def ler_temp_bateria():
    try:
        url = "http://localhost:8085/data.html"  # servidor local do OpenHardwareMonitor
        resposta = requests.get(url)
        soup = BeautifulSoup(resposta.text, "html.parser")
        
        for linha in soup.find_all("tr"):
            colunas = linha.find_all("td")
            if len(colunas) >= 2:
                nome = colunas[0].text.strip()
                valor = colunas[1].text.strip()
                if "Battery" in nome and "°C" in valor:
                    return valor.replace("°C", "").strip()  # Retorna só o número
        return "N/A"
    except Exception:
        return "N/A"
# ================================
# CSV processos
# ================================
def coletar_dados():
    for processo in psutil.process_iter(['pid','name','cpu_percent','memory_percent','status','create_time']):
        try:
            tempo_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pid = processo.info['pid']
            nome = processo.info['name'] or "Desconhecido"
            cpu = processo.info['cpu_percent'] or 0.0
            ram = processo.info['memory_percent'] or 0.0
            status = processo.info['status'] or "indefinido"
            tempo_vida = time.time() - processo.info['create_time']

            df_processos = pd.DataFrame([{
                "Timestamp" : tempo_atual,
                "Pid": pid,
                "Nome": nome,
                "Cpu": cpu,
                "Ram": ram,
                "Status": status,
                "TempoVida": tempo_vida
            }])
            df_processos.to_csv('{id}')
            

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue


# ================================
# Loop de monitoramento
# ================================

tempo = datetime.now()
def monitoramento():
    while tempo != time(22,00):

        print("=" * 120)
        print("\n ", "-" * 45, "Monitoramento do Sistema", "-" * 45, "\n")

        # ======== Coleta geral do sistema ========

        usuario = psutil.users()[0].name if psutil.users() else "Desconhecido"
        porcentagem_cpu = psutil.cpu_percent(interval=1)
        porcentagem_ram = psutil.virtual_memory().percent
        porcentagem_disco = psutil.disk_usage('/').percent
        tempo_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        enderecos = psutil.net_if_addrs()

        # ======== Bateria (se existir) ========
        try:
            bateria_info = psutil.sensors_battery()
            bateria = bateria_info.percent if bateria_info else "N/A"
        except Exception:
            bateria = "N/A"

        # ======== Temperatura da bateria ========
        temperatura_bateria = ler_temp_bateria()
        ######


        # ======== Temperatura da CPU ========

        try:
            temperatura = psutil.sensors_temperatures(fahrenheit=False)
            if 'coretemp' in temperatura and temperatura['coretemp']:
                temperatura_cpu = temperatura['coretemp'][0].current
                print(f"Temperatura da CPU: {temperatura_cpu}°C")
            else:
                temperatura_cpu = 'N/A'
                print("Não foi possível encontrar o sensor de temperatura da CPU ('coretemp').")
        except (AttributeError, KeyError):
            temperatura_cpu = 'N/A'
            print("O sistema não possui suporte para leitura da temperatura da CPU.")

        # ======== Endereço MAC ========

        enderecoMac = None
        interfaces_ignoradas = ['lo', 'docker0', 'virbr0', 'tun0']
        for interface, enderecos_da_interface in enderecos.items():
            if interface not in interfaces_ignoradas:
                for endereco in enderecos_da_interface:
                    if endereco.family == AF_LINK:
                        enderecoMac = endereco.address
                        break
                if enderecoMac:
                    break

    # ======== Processos ========

        qtd_processos = 0
        for p in psutil.process_iter(['pid', 'name']):
            try:
                qtd_processos += 1
                p.cpu_percent(None)  # Inicializa leitura de CPU
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        time.sleep(1)  # Espera 1 segundo para atualização


        # ======== Dados errados ========
        if tempo > 19:
            if porcentagem_cpu < 100 and porcentagem_disco  < 100 and porcentagem_ram  < 100:
                porcentagem_cpu = round(porcentagem_cpu * 4.5, 2)
                porcentagem_ram = round(porcentagem_ram * 1.5, 2)
                porcentagem_disco = round(porcentagem_disco * 1.2, 2)
                temperatura_cpu = round(temperatura_cpu * 1.7, 2)

        # ======== Registro no CSV ========

        df = pd.DataFrame([{
            'timestamp': tempo_atual,
            'endereco_mac': enderecoMac,
            'user': usuario,
            'cpu': porcentagem_cpu,
            'ram': porcentagem_ram,
            'disco': porcentagem_disco,
            'quantidade_processos': qtd_processos,
            'bateria': bateria,
            'temp_cpu': temperatura_cpu,
            'temp_bateria': temperatura_bateria
        }])
        df.to_csv(f"{id}-{timestamp}.csv", mode='a', index=False, header=False)

        # ======== Saída no terminal ========

        print(f"* Usuário conectado: {usuario}")
        print(f"* Uso atual da CPU: {porcentagem_cpu:.1f}%")
        print(f"* Uso atual da RAM: {porcentagem_ram:.1f}%")
        print(f"* Uso atual do Disco: {porcentagem_disco:.1f}%")
        print(f"* Quantidade de Processos: {qtd_processos}")
        print(f"* Porcentagem de Bateria: {bateria}%")
        print(f"* Endereço MAC: {enderecoMac}")
        print(f"* Temperatura CPU: {temperatura_cpu}\n")
        print(f"Temperatura da bateria: {temperatura_bateria}°C")

        print("=" * 120)

        time.sleep(30)
        coletar_dados()
        time.sleep(30)

# ================================
# Upload opcional para AWS S3 (comentar/descomentar)
# ================================

# aws_access_key_id = 'SEU_ACCESS_ID'
# aws_secret_access_key = 'SEU_SECRET_ACCESS_KEY'
# aws_session_token = 'SEU_SESSION_TOKEN'
# aws_region = 'us-east-1'
# usuario = 'SEU_USUARIO'

# session = boto3.Session(
#     aws_access_key_id=aws_access_key_id,
#     aws_secret_access_key=aws_secret_access_key,
#     aws_session_token=aws_session_token,
#     region_name=aws_region
# )

# s3_client = session.client('s3')
# try:
#     response = s3_client.upload_file("captura.csv", "raw", "captura-" + usuario + ".csv")
# except ClientError as e:
#     logging.error(e)
if (datetime.now() != time(22,00)):
    monitoramento()
