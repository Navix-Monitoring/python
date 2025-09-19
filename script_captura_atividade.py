# Importação das bibliotecas necessárias
import psutil  # Para coletar informações sobre o sistema (CPU, RAM, discos, etc.)
import pandas as pd  # Para manipular dados e salvar em CSV
from datetime import datetime, timedelta  # Para trabalhar com datas e horários
import time  # Para fazer pausas no código
import socket  # Para trabalhar com endereços de rede
import os  # Para interagir com o sistema operacional

# Exibição de uma arte com o nome do programa
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

# Criação de um arquivo CSV para armazenar as informações se ele não existir
if not os.path.exists("captura.csv"):
    df_inicial = pd.DataFrame(columns=[
        'timestamp', 'endereco_mac', 'user', 'cpu', 'ram', 'disco', 
        'nucleos_logicos', 'nucleos_fisicos'
    ])
    df_inicial.to_csv("captura.csv", index=False)

# Criação de um arquivo CSV para armazenar os dados dos processos
if not os.path.exists("processos.csv"):
    df_processo = pd.DataFrame(columns=['timestamp','id', 'processo', 'uso_cpu', 'uso_memoria'])
    df_processo.to_csv("processos.csv", index=False)

# Atribui o valor correto para o tipo de família de endereços de rede
AF_LINK = getattr(psutil, "AF_LINK", None) or getattr(socket, "AF_PACKET", None)

# Função para formatar a memória em MB ou GB
def formatar_memoria(valor):
    mb = valor / 1024**2  # Converte o valor para MB
    if mb > 1024:
        return f"{mb/1024:.1f} GB"  # Se for maior que 1 GB, retorna em GB
    else:
        return f"{mb:.0f} MB"  # Caso contrário, retorna em MB

# Laço que roda indefinidamente, monitorando o sistema a cada 10 segundos
while True:
    print("="*120)  # Exibe uma linha de separação
    print("\n ", "-"*45 ,"Monitoramento do Sistema", "-"*45 ,"\n")  # Cabeçalho

    # Coleta de dados do sistema
    usuario = psutil.users()[0].name  # Obtém o nome do usuário
    porcentagem_cpu = psutil.cpu_percent(interval=1)  # Uso da CPU em porcentagem
    porcentagem_ram = psutil.virtual_memory().percent  # Uso da RAM em porcentagem
    porcentagem_disco = psutil.disk_usage('/').percent  # Uso do disco em porcentagem
    tempo_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Hora atual
    processos = list(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']))  # Dados dos processos
    nucleos_logicos = psutil.cpu_count(logical=True)  # Número de núcleos lógicos
    nucleos_fisicos = psutil.cpu_count(logical=False)  # Número de núcleos físicos
    enderecos = psutil.net_if_addrs()  # Endereços de rede

    # Coleta do endereço MAC
    enderecoMac = None
    interfaces_ignoradas = ['lo', 'docker0', 'virbr0', 'tun0']  # Interfaces de rede a serem ignoradas
    for interface, enderecos_da_interface in enderecos.items():
        if interface not in interfaces_ignoradas:
            for endereco in enderecos_da_interface:
                if endereco.family == AF_LINK:  # Se for endereço de link (MAC)
                    enderecoMac = endereco.address
                    break
            if enderecoMac:
                break 

    # Inicializa a coleta de CPU para os processos
    for p in psutil.process_iter(['pid', 'name']):
        p.cpu_percent(None)  # Limpa o histórico de uso de CPU
    time.sleep(1)  # Aguarda 1 segundo para garantir a atualização dos dados
    processos = list(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']))  # Atualiza os dados dos processos

    # Criação de um dataframe com as informações coletadas
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
    df.to_csv('captura.csv', mode='a', index=False, header=False)  # Salva os dados no CSV

    # Ordena os processos pela utilização de CPU e memória
    processosOrdenados_Cpu = sorted(processos, key=lambda p: p.info['cpu_percent'], reverse=True)
    processosOrdenados_Memoria = sorted(processos, key=lambda p: p.info['memory_info'].rss, reverse=True)

    # Coleta e grava as informações sobre os processos mais exigentes
    for processo in processosOrdenados_Cpu:
        dfProcesso = pd.DataFrame([{
            'timestamp': tempo_atual,
            'id': processo.info['pid'],
            'processo': processo.info['name'],
            'uso_cpu': f'{processo.info["cpu_percent"]:.2f}',
            'uso_memoria': f'{processo.info["memory_info"].rss / 1024**2:.2f}'
        }])
        dfProcesso.to_csv('processos.csv', mode='a', index=False, header=False)

    # Exclui processos com o nome "System Idle Process"
    processos_validos = [p for p in processosOrdenados_Cpu if p.info['name'].lower() != "system idle process"]

    # Determina o processo com maior uso de CPU e o de maior uso de memória
    if processos_validos:
        maiorCPU = processos_validos[0]
    else:
        maiorCPU = None  
    maiorMemoria = processosOrdenados_Memoria[0]

    # Exibe as informações coletadas no terminal
    print(f"* Usuário conectado: {usuario}")
    print(f"* Uso atual da CPU: {porcentagem_cpu:.1f}%")
    print(f"* Uso atual da RAM: {porcentagem_ram:.1f}%")
    print(f"* Uso atual do Disco: {porcentagem_disco:.1f}%")
    print(f"* Endereço MAC: {enderecoMac}\n")
    
    # Cálculo do uso de CPU por núcleo lógico
    uso_cpu_processo = maiorCPU.info['cpu_percent'] / nucleos_logicos

    # Exibe o processo que mais consome CPU
    print("-- Programa que mais consome CPU neste momento:")
    print(f"   → ID: {maiorCPU.info['pid']}, Nome: {maiorCPU.info['name']}, Uso de CPU: {uso_cpu_processo:.1f}%\n")

    # Exibe o processo que mais consome memória
    print("-- Programa que mais consome Memória RAM neste momento:")
    print(f"   → ID: {maiorMemoria.info['pid']}, Nome: {maiorMemoria.info['name']}, Memória usada: {formatar_memoria(maiorMemoria.info['memory_info'].rss)}\n")

    # Lê o arquivo CSV de captura e calcula a mediana do uso de CPU e RAM na última hora
    df_leitura = pd.read_csv('captura.csv')
    df_leitura['timestamp'] = pd.to_datetime(df_leitura['timestamp'], format="%Y-%m-%d %H:%M:%S", errors="coerce")

    ultima_hora = df_leitura[df_leitura['timestamp'] >= (df_leitura['timestamp'].max() - timedelta(hours=1))]
    if not ultima_hora.empty:
        media_cpu = ultima_hora['cpu'].median()  # Mediana de uso de CPU na última hora
        media_ram = ultima_hora['ram'].median()  # Mediana de uso de RAM na última hora
        print("-- Mediana de consumo na última hora:")
        print(f"   → CPU: {media_cpu:.1f}%")
        print(f"   → RAM: {media_ram:.1f}%\n")

    print("="*120)  # Linha de separação
    time.sleep(10)  # Espera 10 segundos antes de rodar novamente