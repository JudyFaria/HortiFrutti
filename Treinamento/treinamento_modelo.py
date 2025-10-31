# carregar as imagens 
# treinar modelo
# salvar um arquivo .h5 ou .keras

# -> TRANSFER LEARNING - TensorFlow
#      API Keras (torna trivial)


# pip install tensorflow pillow matplotlib
#  - tensorflow: biblioteca de IA
#  - pillow: para manipulação de imagens
#  - matplotlib: visualização gráficos de treinamento

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers 
from tensorflow.keras.models import Sequential
import matplotlib.pyplot as plt
import os

# Parâmetros
PATH_DATASET = 'Treinamento/imagens'
IMG_HEIGHT = 224
IMG_WIDTH = 224
TAMANHO_LOTE = 32 # processador de 32 em 32 imagens

# Carregar dados
train_dataset = tf.keras.utils.image_dataset_from_directory(
    # cria dataset de validação, checa se o modelo não está decorando as imagens
    PATH_DATASET,
    validation_split = 0.2, #20% para validação
    subset = "training",
    seed = 123, # o é isso?
    image_size = (IMG_HEIGHT, IMG_WIDTH),
    batch_size = TAMANHO_LOTE
)

valid_dataset = tf.keras.utils.image_dataset_from_directory(
    # cria dataset de validação, checa se o modelo não está decorando as imagens
    PATH_DATASET,
    validation_split = 0.2, #20% para validação
    subset = "validation",
    seed = 123, # o é isso?
    image_size = (IMG_HEIGHT, IMG_WIDTH),
    batch_size = TAMANHO_LOTE
)

# pega o nome das clases (as chaves: abacate, cebola, banana...)
class_names = train_dataset.class_names
NUM_CLASS = len(class_names)
print(f"Encontradas {NUM_CLASS} - classes: {class_names}")

# DATA AUGMENTATION
# -> cria "novas" imagens girando, dando zoom, etc, ajudando o modelo a não decorar e ser mais robusto
data_augmentation = keras.Sequential(
    [
        layers.RandomFlip("horizontal", input_shape=(IMG_HEIGHT, IMG_WIDTH, 3)),
        layers.RandomRotation(0.1),
        layers.RandomZoom(0.1),
    ]
)

# Carrega o modelo PRÉ-TREINADO (transfer learning)
# -> MobileNetV2: leve e ótimo para classificação
base_model = tf.keras.applications.MobileNetV2(
    input_shape=(IMG_HEIGHT, IMG_WIDTH, 3),
    include_top=False, #significa que NÃO queremos a camada final original
    weights='imagenet'
)

# -> "congelar" o modelo. Não traina o que ele já sabe
base_model.trainable = False


# --- Criar o modelo final ---
# vamos empilhar as camadas:
#   1. (Opcional) Data Augmentation
#   2. (Opcional) Normalização dos pixels (de 0-255 para 0-1)
#   3. O modelo base (congelado)
#   4. Camada para "achatar" os resultados
#   5. (Opcional) Camada de Dropout para evitar overfitting
#   6. NOSSA camada final: uma camada com neurônios = NUM_CLASSES

model = tf.keras.Sequential(
    [
        data_augmentation,
        layers.Rescaling(1./255), # Normalização
        base_model,
        layers.GlobalAveragePooling2D(), # achata a saída
        layers.Dropout(0.2), # Regularização
        layers.Dense(NUM_CLASS, activation='softmax') 
    ]
)

# Compilar modelo
# -> diz ao modelo como ele deve aprender
model.compile(
    optimizer="adam",
    loss=tf.keras.losses.SparseCategoricalCrossentropy(),
    metrics=['accuracy']
)

print("--- Resumo do Modelo ---")
model.summary()


# TREINAR
print("\n--- Iniciando treinamento ---")

NUM_EPOCAS = 10 
# -> 10 voltas completas no dataset
# -> Se a acurácia estiver subindo, aumentar para 20, 30...

history = model.fit(
    train_dataset,
    validation_data = valid_dataset,
    epochs = NUM_EPOCAS
)

print("\n --- Treinamento Concluído ---")


# Salvar modelo
# -> gera arquivo que usaremos na aplicação
model.save('Treinamento/modelo_hortifrutti.keras')
print(f"Modelo salvo em 'modelo_hortifrutti.keras'")


# Visualizar resultados
acc = history.history['accuracy']
valid_acc = history.history['val_accuracy']

loss = history.history['loss']
valid_loss = history.history['val_loss']

epochs_range = range(NUM_EPOCAS)

plt.figure(figsize=(8,8))
plt.subplot(1, 2, 1)
plt.plot( epochs_range, acc, label='Acurácia de Treino')
plt.plot( epochs_range, valid_acc, label='Acurácia de Validação')
plt.legend(loc='lower right')
plt.title('Acurácia de Treino e Validação')

plt.subplot(1, 2, 1)
plt.plot( epochs_range, loss, label='Perda de Treino')
plt.plot( epochs_range, valid_loss, label='Perda de Validação')
plt.legend(loc='upper right')
plt.title('Perda de Treino e Validação')

# plt.show() -> gerar uma imagem ao invés de mostrar
plt.savefig('grafico_treinamento.png')
print("\nGráfico do treinamento salvo em 'Treinamento/graficos treinamento/grafico_treinamento.png")
