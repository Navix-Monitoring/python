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

df_inicial = pd.DataFrame(columns=['timestamp','user', 'cpu', 'ram', 'disco', 'nucleos_logicos', 'nucleos_fisicos', 'total_processos'])
df_inicial.to_csv("captura.csv", index=False)

while True:
    usuario = psutil.users()[0].name
    porcentagem_cpu = psutil.cpu_percent(interval=1)
    porcentagem_ram = psutil.virtual_memory().percent
    porcentagem_disco = psutil.disk_usage('/').percent
    tempo_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    processos = list(psutil.process_iter())
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

    print("Capturando nome do usuário, cpu, ram, disco, hora atual, total de nucleos e processos inserindo no arquivo 'captura.csv'!\n")
    df.to_csv('captura.csv', mode='a', index=False, header=False)

    print("Captura realizada com sucesso!\n")

    df_leitura = pd.read_csv('captura.csv')
    print("Ultimo dado inserido:\n")
    print(df_leitura[len(df_leitura)-1:])

    ultimosProcessos = processos[-5:]
    print("\nExibição dos ultimos 5 processos (depuração)\n")
    for process in ultimosProcessos:
        print(f"PID: {process.pid}, Nome: {process.name()}")

    time.sleep(10)