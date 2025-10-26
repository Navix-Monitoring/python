# Importação das bibliotecas necessárias
import psutil  # Para coletar informações sobre o sistema (CPU, RAM, discos, etc.)
import pandas as pd  # Para manipular dados e salvar em CSV
from datetime import datetime  # Para trabalhar com datas e horários
import time  # Para fazer pausas no código
import socket  # Para trabalhar com endereços de rede
import os  # Para interagir com o sistema operacional
import logging
import boto3
from botocore.exceptions import ClientError
import csv  # Para registrar o tempo dos processos

# ================================
# Configuração inicial dos arquivos
# ================================

# Criação do arquivo principal de captura
if not os.path.exists("captura.csv"):
    df_inicial = pd.DataFrame(columns=[
        'timestamp', 'endereco_mac', 'user', 'cpu', 'ram', 'disco',
        'quantidade_processos', 'bateria', 'temp_cpu'
    ])
    df_inicial.to_csv("captura.csv", index=False)

# Criação do arquivo de processos
if not os.path.exists("processos.csv"):
    with open("processos.csv", mode="w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["processo", "data_hora", "duracao_segundos"])

# Detecta tipo de família de endereço MAC (compatível Linux/Windows)
AF_LINK = getattr(psutil, "AF_LINK", None) or getattr(socket, "AF_PACKET", None)

# ================================
# Funções auxiliares
# ================================

def registrar_tempo(processo, inicio, fim):
    """Registra a duração de execução de um processo no CSV."""
    duracao = fim - inicio
    with open("processos.csv", mode="a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow([processo, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), round(duracao, 4)])


def formatar_memoria(valor):
    """Converte bytes para MB ou GB formatados."""
    mb = valor / 1024**2
    return f"{mb/1024:.1f} GB" if mb > 1024 else f"{mb:.0f} MB"

# ================================
# Loop de monitoramento
# ================================

tempo = 0

while tempo <= 33:
    inicio_processo = time.time()

    print("=" * 120)
    print("\n ", "-" * 45, "Monitoramento do Sistema", "-" * 45, "\n")

    # ======== Coleta geral do sistema ========

    usuario = psutil.users()[0].name if psutil.users() else "Desconhecido"
    porcentagem_cpu = psutil.cpu_percent(interval=1)
    porcentagem_ram = psutil.virtual_memory().percent
    porcentagem_disco = psutil.disk_usage('/').percent
    tempo_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    enderecos = psutil.net_if_addrs()

    # Bateria (se existir)
    try:
        bateria_info = psutil.sensors_battery()
        bateria = bateria_info.percent if bateria_info else "N/A"
    except Exception:
        bateria = "N/A"

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

    # Nova estrutura de coleta de processos com tempo de execução
    processos = []
    with open("processos.csv", mode="a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo)

        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'create_time']):
            try:
                tempo_execucao = datetime.now() - datetime.fromtimestamp(p.info['create_time'])
                segundos_execucao = tempo_execucao.total_seconds()

                processos.append(p.info)

                escritor.writerow([
                    p.info['name'],
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    round(segundos_execucao, 2)
                ])

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue


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
        'temp_cpu': temperatura_cpu
    }])
    df.to_csv('captura.csv', mode='a', index=False, header=False)

    # ======== Saída no terminal ========

    print(f"* Usuário conectado: {usuario}")
    print(f"* Uso atual da CPU: {porcentagem_cpu:.1f}%")
    print(f"* Uso atual da RAM: {porcentagem_ram:.1f}%")
    print(f"* Uso atual do Disco: {porcentagem_disco:.1f}%")
    print(f"* Quantidade de Processos: {qtd_processos}")
    print(f"* Porcentagem de Bateria: {bateria}%")
    print(f"* Endereço MAC: {enderecoMac}")
    print(f"* Temperatura CPU: {temperatura_cpu}\n")

    print("=" * 120)

    time.sleep(10)
    tempo += 1

    fim_processo = time.time()

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
