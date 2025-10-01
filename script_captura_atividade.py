# Importação das bibliotecas necessárias
import psutil  # Para coletar informações sobre o sistema (CPU, RAM, discos, etc.)
import pandas as pd  # Para manipular dados e salvar em CSV
from datetime import datetime, timedelta  # Para trabalhar com datas e horários
import time  # Para fazer pausas no código
import socket  # Para trabalhar com endereços de rede
import os  # Para interagir com o sistema operacional

# Criação de um arquivo CSV para armazenar as informações se ele não existir
if not os.path.exists("captura.csv"):
    df_inicial = pd.DataFrame(columns=[
        'timestamp', 'endereco_mac', 'user', 'cpu', 'ram', 'disco', 'quantidade_processos'
    ])
    df_inicial.to_csv("captura.csv", index=False)

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
    qtd_processos = 0
    # Inicializa a coleta de CPU para os processos
    for p in psutil.process_iter(['pid', 'name']):
        qtd_processos += 1
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
        'quantidade_processos': qtd_processos
    }])
    df.to_csv('captura.csv', mode='a', index=False, header=False)  # Salva os dados no CSV

    # Exibe as informações coletadas no terminal
    print(f"* Usuário conectado: {usuario}")
    print(f"* Uso atual da CPU: {porcentagem_cpu:.1f}%")
    print(f"* Uso atual da RAM: {porcentagem_ram:.1f}%")
    print(f"* Uso atual do Disco: {porcentagem_disco:.1f}%")
    print(f"* Quantidade de Processos: {qtd_processos}")
    print(f"* Endereço MAC: {enderecoMac}\n")

    print("="*120)  # Linha de separação
    time.sleep(10)  # Espera 10 segundos antes de rodar novamente