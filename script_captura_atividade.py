import psutil
import pandas as pd
from datetime import datetime
import time

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

df_inicial = pd.DataFrame(columns=['timestamp','user', 'cpu', 'ram', 'disco', 'nucleos_logicos', 'nucleos_fisicos'])
df_inicial.to_csv("captura.csv", index=False)


df_processo = pd.DataFrame(columns=['timestamp','id', 'processo', 'uso de cpu', 'uso de memoria'])
df_processo.to_csv("processos.csv", index=False)

while True:
    print("==================================================================================================================")

    print(r"""
        
        ____            _                             _              
    / ___|__ _ _ __ | |_ _   _ _ __ __ _ _ __   __| | ___         
    | |   / _` | '_ \| __| | | | '__/ _` | '_ \ / _` |/ _ \        
    | |__| (_| | |_) | |_| |_| | | | (_| | | | | (_| | (_) | _ _ _ 
    \____\__,_| .__/ \__|\__,_|_|  \__,_|_| |_|\__,_|\___(_|_|_|_)
            |_|                                                 
    
    """)

    usuario = psutil.users()[0].name
    porcentagem_cpu = psutil.cpu_percent(interval=1)
    porcentagem_ram = psutil.virtual_memory().percent
    porcentagem_disco = psutil.disk_usage('/').percent
    tempo_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    processos = list(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']))
    total_processos = len(processos)
    nucleos_logicos = psutil.cpu_count(logical=True)
    nucleos_fisicos = psutil.cpu_count(logical=False)

    df = pd.DataFrame([{
        'timestamp': tempo_atual,
        'user': usuario,
        'cpu': porcentagem_cpu,
        'ram': porcentagem_ram,
        'disco': porcentagem_disco,
        'nucleos_logicos': nucleos_logicos,
        'nucleos_fisicos': nucleos_fisicos,
        'total_processos': total_processos
    }])

    processosOrdenados_Cpu = sorted(
        processos,
        key = lambda p: p.info['cpu_percent'],
        reverse=True
    )

    processosOrdenados_Memoria = sorted(
        processos,
        key = lambda p: p.info['memory_info'],
        reverse=True
    )

    print("________________________________________________________________________________________________________________\n")
    print("Capturando processos e inserindo no arquivo 'processos.csv'\n")
    for processo in processosOrdenados_Cpu:
        dfProcesso = pd.DataFrame([{
            'timestamp': tempo_atual,
            'id': processo.info['pid'],
            'processo': processo.info['name'],
            'uso de cpu': f'{processo.info['cpu_percent']:.2f}',
            'uso de memoria': f'{processo.info['memory_info'].rss / 1024**2:.2f}'
        }])
        dfProcesso.to_csv('processos.csv', mode='a', index=False, header=False)
    
    dfProcesso = pd.read_csv('processos.csv')
    print("Ultimo processo inserido:\n")
    print(f'{dfProcesso[len(dfProcesso)-1:]}\n')

    maiorCPU = processosOrdenados_Cpu[0]
    maiorMemoria = processosOrdenados_Memoria[0]

    print("________________________________________________________________________________________________________________\n")
    time.sleep(1)
    print("Processo com maior uso de CPU:\n")
    print(f"Id do processo: {maiorCPU.info['pid']}, Processo: {maiorCPU.info['name']}, Porcentagem de uso: {maiorCPU.info['cpu_percent']:.2f}%\n")
    print("________________________________________________________________________________________________________________\n")
    
    print("Processo com maior uso de Memória:\n")
    print(f"Id do processo: {maiorMemoria.info['pid']}, Processo: {maiorMemoria.info['name']}, Megas utilizados: {maiorMemoria.info['memory_info'].rss / 1024**2:.2f}MB")

    print("________________________________________________________________________________________________________________\n")
    time.sleep(1)

    print("Capturando nome do usuário, cpu, ram, disco, hora atual, total de nucleos e inserindo no arquivo 'captura.csv'!\n")
    df.to_csv('captura.csv', mode='a', index=False, header=False)
    print("....\n")
    time.sleep(1)
    print("Captura realizada com sucesso!\n")

    df_leitura = pd.read_csv('captura.csv')
    print("Ultimo dado inserido:\n")
    print(f'{df_leitura[len(df_leitura)-1:]}\n')
    print("==================================================================================================================")

    time.sleep(10)