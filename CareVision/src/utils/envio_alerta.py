import pyautogui as auto
import pywhatkit as kit
import time
from geopy.geocoders import Nominatim
from twilio.rest import Client
import datetime

# Credenciais da conta Twilio

# As variáveis que estão marcadas com '#' é referente a dados sensíveis. Caso utilizar o nosso projeto, precisará alterar conforme os seus dados.
sid_conta = "#"
auth_ = "#"
twilio_numero = "#"

def converter_localizacao_para_Maps_link(localizacao_escrita): #função que converte uma localização escrita em um link do Google Maps

    geolocator = Nominatim(user_agent="#", timeout= 10)  #user_agent é o código API, testar outro novamente --- timeout é o tempo máximo de espera para a resposta do servidor

    try:
        location = geolocator.geocode(localizacao_escrita) #geocode converte um endereço em coordenadas geográficas (latitude e longitude)
        if location:
            latitude = location.latitude
            longitude = location.longitude
            print(f"Localização encontrada: Latitude={latitude}, Longitude={longitude}")


            link_Maps = f"https://www.google.com/maps/place/{latitude},{longitude}/@{latitude},{longitude},15z" # 15z é o nível de zoom, cria o link com latitude e longitude
            return link_Maps
        else:
            return "Não foi possível encontrar as coordenadas para a localização fornecida."
    except Exception as e: # trata erros que podem ocorrer durante a geocodificação
        return f"Ocorreu um erro durante a geocodificação: {e}"

def enviar_msg(numero, mensagem): #função de envio de mensagens
    try:
        print(f"Enviando mensagem para {numero}...") #me informa dentro do terminal
        
        kit.sendwhatmsg_instantly(numero, mensagem, wait_time= 10, tab_close=True)#abre o whats web, identifica o numero, escreve a mensagem, espera 10 segundos, envia e fecha o whats

        auto.press('enter')
        print(f"Mensagem enviada para {numero} com sucesso!")
    except Exception as e:
        print(f"Ocorreu um erro ao enviar a mensagem para {numero}: {e}")

def acionar_alerta_emergencia(tipo, envolvidos, fogo, local):
    
    agora = datetime.datetime.now() #pega a data e a hora atual
    data_hora = agora.strftime('%d/%m/%Y    %H:%M:%S') #Converto para um formato mais legível, dia/mês/ano hora:minuto:segundo
    client = Client(sid_conta, auth_)#criaçao da chamada do cliente com as credenciais
    link_maps = converter_localizacao_para_Maps_link(local)

    if fogo:
        mensagem = (f"⚠️ *ALERTA* \nColisão: {tipo}\nCom fogo \nEnvolvendo {envolvidos} carros.\n{data_hora}\nLocal: *{local}*\n{link_maps}")
        mensagem_liagacao = f"""
            <Response>
            <Say language="pt-BR" voice="alice">
            Olá, está é uma chamada automatizada. 
            Houve uma acidente {tipo} com fogo no local, envolvendo {envolvidos} carros na {local} FATEC RIO CLARO, mande uma viatura, uma ambulância e o corpo de bombeiros até o local com urgência.
            Obrigado por atender. Até mais!
            </Say>
            </Response>
            """
    else:
        mensagem = (f"⚠️ *ALERTA* \nHouve colisão {tipo}, envolvendo {envolvidos} carros.\n{data_hora}\nLocal: *{local}*\n{link_maps}")
        mensagem_liagacao = f"""
            <Response>
            <Say language="pt-BR" voice="alice">
            Olá, está é uma chamada automatizada. 
            Houve uma acidente {tipo}, envolvendo {envolvidos} carros na {local} FATEC RIO CLARO, mande uma viatura e uma ambulancia até o local com urgência.
            Obrigado por atender. Até mais!
            </Say>
            </Response>
            """

    lista_numeros = ["#"]
    print("Iniciando o envio de mensagens...")

    for numero in lista_numeros:
        enviar_msg(numero, mensagem)
        time.sleep(10)
        ligacao = client.calls.create(
            to = lista_numeros, 
            from_ = twilio_numero,
            twiml = mensagem_liagacao
        )
    print(f"Ligação enviada para {numero}")