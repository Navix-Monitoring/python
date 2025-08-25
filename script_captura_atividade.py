import psutil
import pandas as pd
from datetime import datetime
import time

df_inicial = pd.DataFrame(columns=['timestamp','user', 'cpu', 'ram', 'disco'])
df_inicial.to_csv("captura.csv", index=False)

while True:
    usuario = psutil.users()[0].name
    porcentagem_cpu = psutil.cpu_percent(interval=1)
    porcentagem_ram = psutil.virtual_memory().percent
    porcentagem_disco = psutil.disk_usage('/').percent
    tempo_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    df = pd.DataFrame([{
        'timestamp': tempo_atual,
        'user': usuario,
        'cpu': porcentagem_cpu,
        'ram': porcentagem_ram,
        'disco': porcentagem_disco
    }])

    df.to_csv('captura.csv', mode='a', index=False, header=False)

    time.sleep(10)