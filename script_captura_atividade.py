import psutil
import pandas as pd
from datetime import datetime, timedelta
import time
import socket
import os

print(r"""
 ___       _      _                 _       
|_ _|_ __ (_) ___(_) __ _ _ __   __| | ___  
 | || '_ \| |/ __| |/ _` | '_ \ / _` |/ _ \ 
 | || | | | | (__| | (_| | | | | (_| | (_) |
|___|_| |_|_|\___|_|\__,_|_| |_|\__,_|\___/ 
  ___ __ _ _ __ | |_ _   _ _ __ __ _        
 / __/ _` | '_ \| __| | | | '__/ _` |       
| (_| (_| | |_) | |_| |_| | | | (_| |_ _ _  
 \___\__,_| .__/ \__|\__,_|_|  \__,_(_|_|_) 
          |_|                                            
""")

if not os.path.exists("captura.csv"):
    df_inicial = pd.DataFrame(columns=[
        'timestamp', 'endereco_mac', 'user', 'cpu', 'ram', 'disco', 
        'nucleos_logicos', 'nucleos_fisicos'
    ])
    df_inicial.to_csv("captura.csv", index=False)

if not os.path.exists("processos.csv"):
    df_processo = pd.DataFrame(columns=['timestamp','id', 'processo', 'uso_cpu', 'uso_memoria'])
    df_processo.to_csv("processos.csv", index=False)

AF_LINK = getattr(psutil, "AF_LINK", None) or getattr(socket, "AF_PACKET", None)

def formatar_memoria(valor):
    mb = valor / 1024**2
    if mb > 1024:
        return f"{mb/1024:.1f} GB"
    else:
        return f"{mb:.0f} MB"

while True:
    print("="*120)
    print("\n ", "-"*45 ,"Monitoramento do Sistema", "-"*45 ,"\n")

    usuario = psutil.users()[0].name
    porcentagem_cpu = psutil.cpu_percent(interval=1)
    porcentagem_ram = psutil.virtual_memory().percent
    porcentagem_disco = psutil.disk_usage('/').percent
    tempo_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    processos = list(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']))
    nucleos_logicos = psutil.cpu_count(logical=True)
    nucleos_fisicos = psutil.cpu_count(logical=False)
    enderecos = psutil.net_if_addrs()

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

    df = pd.DataFrame([{
        'timestamp': tempo_atual,
        'endereco_mac': enderecoMac,
        'user': usuario,
        'cpu': porcentagem_cpu,
        'ram': porcentagem_ram,
        'disco': porcentagem_disco,
        'nucleos_logicos': nucleos_logicos,
        'nucleos_fisicos': nucleos_fisicos
    }])
    df.to_csv('captura.csv', mode='a', index=False, header=False)

    processosOrdenados_Cpu = sorted(
        processos,
        key=lambda p: p.info['cpu_percent'], reverse=True
    )
    processosOrdenados_Memoria = sorted(
        processos,
        key=lambda p: p.info['memory_info'].rss,
        reverse=True
    )

    for processo in processosOrdenados_Cpu:
        dfProcesso = pd.DataFrame([{
            'timestamp': tempo_atual,
            'id': processo.info['pid'],
            'processo': processo.info['name'],
            'uso_cpu': f'{processo.info["cpu_percent"]:.2f}',
            'uso_memoria': f'{processo.info["memory_info"].rss / 1024**2:.2f}'
        }])
        dfProcesso.to_csv('processos.csv', mode='a', index=False, header=False)

    processos_validos = [p for p in processosOrdenados_Cpu if p.info['name'].lower() != "system idle process"]

    if processos_validos:
        maiorCPU = processos_validos[0]
    else:
        maiorCPU = None  
    maiorMemoria = processosOrdenados_Memoria[0]

    print(f"* Usuário conectado: {usuario}")
    print(f"* Uso atual da CPU: {porcentagem_cpu:.1f}%")
    print(f"* Uso atual da RAM: {porcentagem_ram:.1f}%")
    print(f"* Uso atual do Disco: {porcentagem_disco:.1f}%")
    print(f"* Endereço MAC: {enderecoMac}\n")
    
    uso_cpu_processo = maiorCPU.info['cpu_percent'] / nucleos_logicos

    print("-- Programa que mais consome CPU neste momento:")
    print(f"   → ID: {maiorCPU.info['pid']}, Nome: {maiorCPU.info['name']}, Uso de CPU: {uso_cpu_processo:.1f}%\n")

    print("-- Programa que mais consome Memória RAM neste momento:")
    print(f"   → ID: {maiorMemoria.info['pid']}, Nome: {maiorMemoria.info['name']}, Memória usada: {formatar_memoria(maiorMemoria.info['memory_info'].rss)}\n")

    df_leitura = pd.read_csv('captura.csv')
    df_leitura['timestamp'] = pd.to_datetime(df_leitura['timestamp'], format="%Y-%m-%d %H:%M:%S", errors="coerce")

    ultima_hora = df_leitura[df_leitura['timestamp'] >= (df_leitura['timestamp'].max() - timedelta(hours=1))]
    if not ultima_hora.empty:
        media_cpu = ultima_hora['cpu'].mean()
        media_ram = ultima_hora['ram'].mean()
        print("-- Consumo médio na última hora:")
        print(f"   → CPU: {media_cpu:.1f}%")
        print(f"   → RAM: {media_ram:.1f}%\n")

    print("="*120)
    time.sleep(10)