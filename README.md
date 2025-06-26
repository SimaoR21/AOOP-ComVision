# AOOP-ComVision

# Posture Monitoring for Ergonomics

Projeto desenvolvido por **Simão Rodrigues**, nº **29069**, do curso de **Engenharia Informática (EI)**, no âmbito da unidade curricular de **AOOP**.

##  Descrição

Este programa permite monitorizar a postura corporal de uma pessoa em tempo real, através da webcam, utilizando as bibliotecas **MediaPipe** e **OpenCV**. O objetivo é identificar problemas comuns de postura, como:
- Cabeça inclinada
- Ombros desnivelados
- Coluna torta

Quando algum destes desvios é detetado, o programa exibe alertas visuais diretamente na imagem.

##  Requisitos

- Python 3 instalado no sistema

##  Instalação das dependências

Antes de correr o programa, instale as bibliotecas necessárias com o seguinte comando:

pip install mediapipe opencv-python

##  Como executar

1. Garante que tens uma câmara ligada ao computador.
2. Corre o ficheiro Python que contém o código (main.py):

python main.py

#  LLMs & MMLMs

##  Descrição

Este projeto utiliza a API do OpenRouter com o modelo "mistralai/mistral-7b-instruct" para gerar feedback personalizado sobre postura corporal, baseado em alertas detectados. A função get_llm_feedback envia os problemas identificados (como cabeça inclinada, ombros desnivelados ou coluna torta) e recebe sugestões concisas. O feedback é processado em tempo real, exibido na interface com OpenCV, e atualizado a cada 5 segundos se os alertas mudarem, utilizando um thread separado para gerenciar as chamadas à API de forma assíncrona.

##  Instalações

Antes de correr o programa, corra o seguinte comando:

pip install -r requirements.txt

##  Como executar

1. Garante que tens uma câmara ligada ao computador.
2. Poderá ter de alterar a key da api.
3. Corre o ficheiro Python que contém o código (main.py):

python main.py