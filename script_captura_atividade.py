# Importação das bibliotecas necessárias
import psutil  # Para coletar informações sobre o sistema
import pandas as pd  # Para manipular dados e salvar em CSV
from datetime import datetime, time
import time as sleep_timer  # Para pausas
import socket  # Para endereços de rede
import os  # Sistema operacional
import csv  # Manipulação de CSV
import random # Para variação aleatória da velocidade e simulação

# ================================
# Configuração inicial
# ================================
id_carro = 3
timestamp_inicio = datetime.now().strftime("%Y-%m-%d")

# Variável global para armazenar o estado anterior da bateria (para cálculo de consumo)
bateria_anterior = None 

# Criação do arquivo principal de captura 
nome_arquivo_principal = f"{id_carro}-{timestamp_inicio}.csv"
if not os.path.exists(nome_arquivo_principal):
    df_inicial = pd.DataFrame(columns=[
        'timestamp', 'endereco_mac', 'cpu', 'ram', 'disco',
        'quantidade_processos', 'bateria', 'temp_cpu', 'temp_bateria',
        'velocidade_estimada_kmh', 'consumo_energia' 
    ])
    df_inicial.to_csv(nome_arquivo_principal, index=False)

# Criação do arquivo de processos
nome_arquivo_processos = f"{id_carro}_processos_{timestamp_inicio}.csv"
if not os.path.exists(nome_arquivo_processos):
    with open(nome_arquivo_processos, mode="w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["Timestamp", "Pid", "Nome","Cpu","Ram","TempoVida", "BytesLidos", "BytesEscritos" ])

# Detecta tipo de família de endereço MAC
AF_LINK = getattr(psutil, "AF_LINK", None) or getattr(socket, "AF_PACKET", None)

# ================================
# Funções auxiliares
# ================================

def formatar_memoria(valor):
    """Converte bytes para MB ou GB formatados."""
    mb = valor / 1024**2
    return f"{mb/1024:.1f} GB" if mb > 1024 else f"{mb:.0f} MB"

def ler_temp_bateria(temp_cpu_referencia=None):
    """
    Lê a temperatura exclusivamente através do sensor 'acpitz'.
    """
    try:
        temps = psutil.sensors_temperatures()
        # Busca específica pelo sensor acpitz
        if 'acpitz' in temps and len(temps['acpitz']) > 0:
            return temps['acpitz'][0].current
    except Exception:
        pass

    # Retorna N/A se não encontrar o sensor acpitz, sem simulação
    return "N/A"

def coletar_processos(tempo_atual):
    for processo in psutil.process_iter(['pid','name','cpu_percent','memory_percent','create_time','io_counters']):
        try:

            pid = processo.info['pid']
            nome = processo.info['name'] or "Desconhecido"
            cpu = processo.info['cpu_percent'] or 0.0
            ram = processo.info['memory_percent'] or 0.0
            tempo_vida = sleep_timer.time() - processo.info['create_time']
            io_contadores = processo.info.get('io_counters')
            bytes_lidos = 0
            bytes_escritos = 0
            if io_contadores:
                bytes_lidos = io_contadores.read_bytes
                bytes_escritos = io_contadores.write_bytes
            
            if(cpu>0.0 or ram>1.0):
                dados_processos = pd.DataFrame([{
                    "Timestamp" : tempo_atual,
                    "Pid": pid,
                    "Nome": nome,
                    "Cpu": cpu,
                    "Ram": ram,
                    "TempoVida": tempo_vida,
                    "BytesLidos": bytes_lidos,
                    "BytesEscritos": bytes_escritos
                }])
                dados_processos.to_csv(nome_arquivo_processos, mode='a', index=False, header=False)
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue


# ================================
# Loop de monitoramento
# ================================
tempo = datetime.now().time()

def monitoramento():
    global bateria_anterior # Necessário para modificar a variável global
    
    while tempo != time(22, 0, 0):

        print("=" * 120)
        print("\n ", "-" * 45, "Monitoramento do Sistema (Carro)", "-" * 45, "\n")

        tempo_atual_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ======== Coleta Hardware ========
        porcentagem_cpu = psutil.cpu_percent(interval=1)
        porcentagem_ram = psutil.virtual_memory().percent
        porcentagem_disco = psutil.disk_usage('/').percent
        
        # MAC Address
        enderecos = psutil.net_if_addrs()
        enderecoMac = None
        interfaces_ignoradas = ['lo', 'docker0', 'virbr0', 'tun0']
        for interface, enderecos_da_interface in enderecos.items():
            if interface not in interfaces_ignoradas:
                for endereco in enderecos_da_interface:
                    if endereco.family == AF_LINK:
                        enderecoMac = endereco.address
                        break
                if enderecoMac: break

        # ======== Bateria & Consumo ========
        try:
            bateria_obj = psutil.sensors_battery()
            bateria_atual = bateria_obj.percent if bateria_obj else 100 # Default 100 se não tiver bateria (desktop)
            esta_carregando = bateria_obj.power_plugged if bateria_obj else True
        except Exception:
            bateria_atual = 100
            esta_carregando = True

        # --- Lógica de Simulação de Consumo ---
        # O consumo é a diferença da bateria atual para a anterior.
        consumo_energia = 0.0
        if bateria_anterior is not None:
            diff = bateria_anterior - bateria_atual
            # Se diff > 0, bateria caiu (consumiu). Se diff < 0, carregou.
            if diff > 0:
                consumo_energia = diff
            else:
                consumo_energia = 0.0 # Carregando ou estável
        
        bateria_anterior = bateria_atual
        
        # Se for desktop (sem bateria caindo), simula um consumo flutuante baseado na CPU
        if bateria_atual == 100 or esta_carregando:
             consumo_energia = (porcentagem_cpu * 0.1) + random.uniform(0.5, 2.0)


        # ======== Temperatura CPU ========
        try:
            temperatura = psutil.sensors_temperatures(fahrenheit=False)
            # Tenta pegar 'coretemp' (Intel) ou 'k10temp' (AMD) ou o primeiro disponível
            temperatura_cpu = 'N/A'
            if 'coretemp' in temperatura:
                temperatura_cpu = temperatura['coretemp'][0].current
            elif 'k10temp' in temperatura:
                temperatura_cpu = temperatura['k10temp'][0].current
            elif len(temperatura) > 0:
                primeira_chave = list(temperatura.keys())[0]
                if temperatura[primeira_chave]:
                     temperatura_cpu = temperatura[primeira_chave][0].current
        except Exception:
            temperatura_cpu = 45.0 # Valor seguro caso falhe tudo para não quebrar a simulação da bateria

        # ======== Temperatura Bateria (Nova Lógica) ========
        # Passamos a temperatura da CPU para ajudar na simulação se o sensor real falhar
        valor_temp_cpu_num = temperatura_cpu if isinstance(temperatura_cpu, (int, float)) else 45.0
        temperatura_bateria = ler_temp_bateria(valor_temp_cpu_num)


        # ======== Simulação de Velocidade ========
        # Lógica: Base 40km/h + (Uso de CPU * Fator) + Variação Aleatória
        # Isso cria picos de velocidade quando o computador "pensa" mais
        velocidade_simulada = 40 + (porcentagem_cpu * 1.5) + random.uniform(-5, 15)
        if velocidade_simulada < 0: velocidade_simulada = 0


        # ======== Processos (Contagem apenas) ========
        qtd_processos = len(psutil.pids())

        # Coleta detalhada de processos (opcional, pode pesar no loop se for muito rápido)
        # coletar_processos(tempo_atual_str) 

        # ======== Registro no CSV ========
        df = pd.DataFrame([{
            'timestamp': tempo_atual_str,
            'endereco_mac': enderecoMac,
            'cpu': porcentagem_cpu,
            'ram': porcentagem_ram,
            'disco': porcentagem_disco,
            'quantidade_processos': qtd_processos,
            'bateria': bateria_atual,
            'temp_cpu': temperatura_cpu,
            'temp_bateria': temperatura_bateria,
            'velocidade_estimada_kmh': round(velocidade_simulada, 2),
            'consumo_energia': round(consumo_energia, 4)
        }])
        
        df.to_csv(nome_arquivo_principal, mode='a', index=False, header=False)

        # ======== Saída no terminal ========
        print(f"* Timestamp: {tempo_atual_str}")
        print(f"* CPU: {porcentagem_cpu:.1f}% | Temp CPU: {temperatura_cpu}")
        print(f"* Bateria: {bateria_atual}% | Temp Bat: {temperatura_bateria}°C")
        print(f"* Vel. Simulada: {velocidade_simulada:.1f} km/h")
        print(f"* Processos: {qtd_processos}")
        
        # Pausa do loop (60 segundos conforme seu original)
        coletar_processos(tempo_atual_str)
        sleep_timer.sleep(60)

if __name__ == "__main__":
    try:
        monitoramento()
    except KeyboardInterrupt:
        print("\nMonitoramento encerrado pelo usuário.")
        
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
#     response = s3_client.upload_file(f"{id}-{timestamp}.csv", "raw", id + "-" + timestamp + ".csv")
# except ClientError as e:
#     logging.error(e)

if tempo != time(22,00,00):
    monitoramento()
