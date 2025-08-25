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

df_inicial = pd.DataFrame(columns=['timestamp','user', 'cpu', 'ram', 'disco'])
df_inicial.to_csv("captura.csv", index=False)

while True:
    usuario = psutil.users()[0].name
    porcentagem_cpu = psutil.cpu_percent(interval=1)
    porcentagem_ram = psutil.virtual_memory().percent
    porcentagem_disco = psutil.disk_usage('/').percent
    tempo_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    processos = list(psutil.process_iter())

    df = pd.DataFrame([{
        'timestamp': tempo_atual,
        'user': usuario,
        'cpu': porcentagem_cpu,
        'ram': porcentagem_ram,
        'disco': porcentagem_disco
    }])

    df.to_csv('captura.csv', mode='a', index=False, header=False)

    print("Dados capturados e inseridos no arquivo 'captura.csv'!\n")

    ultimosProcessos = processos[-10:] 
    print("Exibição dos ultimos 10 processos (depuração)\n")
    for process in ultimosProcessos:
        print(f"PID: {process.pid}, Nome: {process.name()}")

    time.sleep(10)