# Projeto CareVision

O CareVision é um sistema inovador de visão computacional projetado para monitorar e detectar automaticamente veículos e acidentes em transmissões de vídeo. Utilizando tecnologias avançadas como YOLO (You Only Look Once) para detecção de objetos e DeepSort para rastreamento, o projeto visa aumentar a segurança e a eficiência na vigilância de áreas críticas, como rodovias.

## Propósito do Projeto

O objetivo principal do CareVision é fornecer uma solução automatizada para:
- **Detecção de Veículos**: Identificar e rastrear diferentes tipos de veículos em tempo real.
- **Detecção de Acidentes**: Reconhecer padrões que indicam colisões ou paradas inesperadas de veículos, acionando alertas.
- **Monitoramento Contínuo**: Oferecer uma interface para visualização das câmeras e dos eventos detectados.

## Estrutura do Projeto

O projeto é organizado nas seguintes pastas principais:

- `src/`: Contém o código-fonte principal da aplicação.
  - `detectors/`: Módulos para detecção de veículos e acidentes (`Detector.py`).
  - `models/`: Armazena os modelos YOLO pré-treinados (`drone.pt`, `modelomaquete.pt`).
  - `utils/`: Funções utilitárias, incluindo configurações (`config.py`) e envio de alertas (`envio_alerta.py`).
  - `data/`: Contém subpastas para dados de entrada (vídeos, imagens) e saída (frames de acidentes detectados).
  - `Interface.py`: O arquivo principal da interface gráfica do usuário (GUI).
- `tests/`: Contém scripts e arquivos para testes.
- `requirements.txt`: Lista todas as dependências Python necessárias para o projeto.

## Tecnologias Utilizadas

- **Python**: Linguagem de programação principal.
- **Ultralytics YOLO**: Framework para detecção de objetos em tempo real.
- **DeepSort**: Algoritmo para rastreamento de múltiplos objetos.
- **OpenCV**: Biblioteca para processamento de imagem e vídeo.
- **PyQt5**: Framework para construção da interface gráfica do usuário.
- **NumPy**: Para operações numéricas eficientes.
- **Pandas**: Para manipulação e análise de dados.
- **Matplotlib**: Para geração de gráficos e visualizações de dados.

## Como Executar (Visão Geral)

Para executar o projeto CareVision, você precisaria:
1.  **Clonar o Repositório**: Obter o código-fonte do projeto.
2.  **Instalar Dependências**: Instalar todas as bibliotecas listadas em `requirements.txt`.
3.  **Modelos Pré-treinados**: Garantir que os modelos YOLO (`drone.pt` e `modelomaquete.pt`) estejam presentes na pasta `src/models/`. Estes modelos são essenciais para a funcionalidade de detecção.
4.  **Executar a Interface**: Iniciar a aplicação através do arquivo `Interface.py`.

## Métricas e Desempenho do Modelo

Para avaliar o desempenho de um modelo de visão computacional como o CareVision, diversas métricas são importantes. Embora o projeto em si não gere logs de métricas de treinamento diretamente, podemos inferir e simular o tipo de dados que seriam relevantes para sua avaliação.

### Métricas Operacionais (Simuladas)

As seguintes métricas são cruciais para entender o comportamento do sistema em tempo real:
-   **Velocidade dos Veículos**: A velocidade estimada dos veículos rastreados ao longo do tempo. Isso pode indicar padrões de tráfego ou anomalias.
-   **Frames Parado**: O número de frames consecutivos em que um veículo permanece parado. Um alto número pode indicar um veículo estacionado ou um acidente.
-   **IoU (Intersection over Union)**: Mede a sobreposição entre as caixas delimitadoras de dois objetos. Um IoU alto entre veículos pode indicar uma colisão.
-   **Confiança das Detecções**: A probabilidade atribuída pelo modelo YOLO de que uma detecção está correta. Uma alta confiança indica detecções mais robustas.

### Métricas de Avaliação do Modelo (Simuladas)

Para avaliar a qualidade do modelo de detecção de acidentes, métricas padrão em visão computacional são utilizadas:
-   **Precisão (Precision)**: A proporção de detecções positivas corretas (verdadeiros positivos) em relação ao total de detecções positivas (verdadeiros positivos + falsos positivos). Indica quão confiável é o modelo em suas previsões.
-   **Recall (Sensibilidade)**: A proporção de detecções positivas corretas (verdadeiros positivos) em relação ao total de casos positivos reais (verdadeiros positivos + falsos negativos). Indica a capacidade do modelo de encontrar todas as instâncias relevantes.
-   **mAP (mean Average Precision)**: Uma métrica comum para avaliação de modelos de detecção de objetos, que considera tanto a precisão quanto o recall em diferentes limiares de confiança e IoU. Um mAP mais alto indica um desempenho geral superior do modelo.

## Visualizações das Métricas

Abaixo estão exemplos de visualizações que representam as métricas discutidas, geradas a partir de dados sintéticos para ilustrar o tipo de análise que pode ser feita:

![Confidence Distribution](https://private-us-east-1.manuscdn.com/sessionFile/MDnHYrxTQIql3g59s0setd/sandbox/UHw1VmHPNrj61z0ZsWHPZk-images_1750093904443_na1fn_L2hvbWUvdWJ1bnR1L1Byb2pldG9fQ2FyZVZpc2lvbi9wbG90cy9jb25maWRlbmNlX2Rpc3RyaWJ1dGlvbg.png?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9wcml2YXRlLXVzLWVhc3QtMS5tYW51c2Nkbi5jb20vc2Vzc2lvbkZpbGUvTURuSFlyeFRRSXFsM2c1OXMwc2V0ZC9zYW5kYm94L1VIdzFWbUhQTnJqNjF6MFpzV0hQWmstaW1hZ2VzXzE3NTAwOTM5MDQ0NDNfbmExZm5fTDJodmJXVXZkV0oxYm5SMUwxQnliMnBsZEc5ZlEyRnlaVlpwYzJsdmJpOXdiRzkwY3k5amIyNW1hV1JsYm1ObFgyUnBjM1J5YVdKMWRHbHZiZy5wbmciLCJDb25kaXRpb24iOnsiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE3NjcyMjU2MDB9fX1dfQ__&Key-Pair-Id=K2HSFNDJXOU9YS&Signature=Oo0hzL2h8tnnC2vNMusakeiXDL67BjyXrTc642MSeWTAbqb2BXVI-VffqYGO1fDsj6H71vjqe8USz4wEF4t04IvcCE1thJbdj2baLFIucV0FII2ymRvIYuQ9jXS0sBFodMi5MRPmfH3eP5ULzkt-fD8ll6LM5~ezVT3B42lh7E43bpmXKAGcf81dVXUIkRzc9INfzlXRwA86el9ChaclOpQEpMmne0d~fP9JHQUiP7gfck4ER7LGXFsKDglFcGCF9hOw-pZJl0rUxbKzYaQLXWqw~wcaXjmF0Oj7KdNtwGGZuQH7jzvWGYvhQYXlEOkUdbeTNiIkDkIsNNkz65p4jA__)
*Histograma da distribuição da confiança das detecções YOLO, mostrando a robustez das identificações do modelo.*

### Métricas de Desempenho do Modelo

![Model Performance Metrics](https://private-us-east-1.manuscdn.com/sessionFile/MDnHYrxTQIql3g59s0setd/sandbox/UHw1VmHPNrj61z0ZsWHPZk-images_1750093904444_na1fn_L2hvbWUvdWJ1bnR1L1Byb2pldG9fQ2FyZVZpc2lvbi9tb2RlbF9wbG90cy9tb2RlbF9wZXJmb3JtYW5jZV9tZXRyaWNz.png?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9wcml2YXRlLXVzLWVhc3QtMS5tYW51c2Nkbi5jb20vc2Vzc2lvbkZpbGUvTURuSFlyeFRRSXFsM2c1OXMwc2V0ZC9zYW5kYm94L1VIdzFWbUhQTnJqNjF6MFpzV0hQWmstaW1hZ2VzXzE3NTAwOTM5MDQ0NDRfbmExZm5fTDJodmJXVXZkV0oxYm5SMUwxQnliMnBsZEc5ZlEyRnlaVlpwYzJsdmJpOXRiMlJsYkY5d2JHOTBjeTl0YjJSbGJGOXdaWEptYjNKdFlXNWpaVjl0WlhSeWFXTnoucG5nIiwiQ29uZGl0aW9uIjp7IkRhdGVMZXNzVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNzY3MjI1NjAwfX19XX0_&Key-Pair-Id=K2HSFNDJXOU9YS&Signature=NV7wmhrn0FRUsCFm0bY0t2xwhKC93luVx75FYHhhUuAdjSTGnXDh0-ky3IJeC9HiBZRmAG9PVkgVLY3Nt-czbswmkP8soq-CjEkOh4yE8oLhqrvvAHvZj6kFwMX~Jnezet6zQVf3V4WO8Aa4yX6z1ugnYJF6xero8fjfVT6CcO-blWKLp5tUediHFiV1YcrKObqmku52WcOwL3zWF5MLRRZ1zaIpUtSyMPYoOn4JFk-k~woQgS6T0kriTsU2W6IFkCG2QhROMEN67RZHI2p1ZAz9E42-xK-dhQxXJuNHGisdXp5kCbmsRYW9FwY34WbLOCzL0brGE7YMWy0YPn8yXA__)
*Gráfico de Precisão, Recall e mAP ao longo das épocas de treinamento (dados sintéticos), ilustrando a evolução do desempenho do modelo.*

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir um pull request ou relatar problemas.

## Licença

Este projeto está licenciado sob a MIT License.




## Colaboradores

- [MateusJoga](https://github.com/MateusJoga)
- [Gijo-0](https://github.com/Gijo-0)
- [eduardocamargoo](https://github.com/eduardocamargoo)
- [vrenzd](https://github.com/vrenzd)


