# CareVision Project

CareVision é um projeto desenvolvido para detectar veículos e acidentes em vídeos utilizando técnicas de visão computacional. Este projeto utiliza modelos YOLO para detecção de objetos e DeepSort para rastreamento.

## Estrutura do Projeto

- **src/**: Contém o código-fonte do projeto.
  - **detectors/**: Implementações dos detectores de veículos e acidentes.
  - **models/**: Modelos YOLO utilizados para detecção.
  - **utils/**: Funções utilitárias, como processamento de vídeo.
  - **main.py**: Ponto de entrada do aplicativo.

- **tests/**: Contém os testes automatizados para o projeto.

- **data/**: Diretório para armazenar dados de entrada e saída.
  - **input/videos/**: Vídeos de entrada para processamento.
  - **output/processed/**: Vídeos processados e resultados.

- **requirements.txt**: Lista de dependências do projeto.

## Como Executar

1. Clone o repositório.
2. Instale as dependências com `pip install -r requirements.txt`.
3. Execute o aplicativo com `python src/main.py`.

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir um pull request ou relatar problemas.

## Licença

Este projeto está licenciado sob a MIT License.