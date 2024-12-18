# -*- coding: utf-8 -*-
import sys
import time
import torch
import faiss
import pathlib
from PIL import Image
import numpy as np
import pandas as pd
import os
import time

import streamlit as st
from streamlit_cropper import st_cropper

sys.path.append(os.path.join(os.getcwd(), 'cbir'))

from features_extractor import (
    calcular_histograma_color,
    calcular_texturas,
    calcular_momentos_hu,
    calcular_cnn,
    calcular_sift,
    promedio_descriptores_sift,
    DB_PATH
)
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Configuración de Streamlit
st.set_page_config(layout="wide")

# Ruta a las imágenes y archivos de índices
FILES_PATH = str(pathlib.Path().resolve())
IMAGES_PATH = os.path.join(FILES_PATH, 'train')

# Porcentajes
TRAIN_CSV = os.path.join(FILES_PATH, 'image_dataset_with_labels_train.csv')  # CSV con las etiquetas de las imágenes
# Cargar el dataset de entrenamiento
train_df = pd.read_csv(TRAIN_CSV)

# Cargar índices FAISS desde DB_PATH
index_color = faiss.read_index(os.path.join(DB_PATH, 'color_histogram.index'))
index_textura = faiss.read_index(os.path.join(DB_PATH, 'texture_descriptor.index'))
index_forma = faiss.read_index(os.path.join(DB_PATH, 'shape_descriptor.index'))
index_cnn = faiss.read_index(os.path.join(DB_PATH, 'cnn_descriptor.index'))
index_sift = faiss.read_index(os.path.join(DB_PATH, 'sift_descriptor.index'))

def get_image_list():
    return [f for f in os.listdir(IMAGES_PATH) if f.lower().endswith(('jpg', 'png', 'jpeg'))]


def retrieve_image(img_query, feature_extractor, n_imgs=11):
    img_array = np.array(img_query)

    # Seleccionar índice y calcular características
    if feature_extractor == 'Color':
        feature_vector = calcular_histograma_color(img_array)
        indexer = index_color
    elif feature_extractor == 'Textura':
        feature_vector = calcular_texturas(img_array)
        indexer = index_textura
    elif feature_extractor == 'Forma':
        feature_vector = calcular_momentos_hu(img_array)[0]  # Solo momentos de Hu
        indexer = index_forma
    elif feature_extractor == 'CNN':
        feature_vector = calcular_cnn(img_array)  # Solo momentos de Hu
        indexer = index_cnn
    elif feature_extractor == 'SIFT':
        _, sift_descriptors = calcular_sift(img_array)
        feature_vector = promedio_descriptores_sift(sift_descriptors)
        indexer = index_sift

    else:
        raise ValueError(f"Extractor desconocido: {feature_extractor}")

    # Preparar el vector para la búsqueda
    vector = np.array(feature_vector).astype('float32').reshape(1, -1)

    # Buscar las imágenes más similares
    _, indices = indexer.search(vector, k=n_imgs)

    return indices[0]

#METRICAS
def calculate_metrics(query_label, retrieved_labels, k):
    # Calcular True Positives
    true_positives = sum(1 for label in retrieved_labels if label == query_label)
    total_relevant = train_df[train_df['Category'] == query_label].shape[0]

    # Precision@K
    precision = true_positives / k if k > 0 else 0

    # Recall@K
    recall = true_positives/ total_relevant if total_relevant > 0 else 0

    # F1-Score@K
    f1 = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0
    )

    print(f"Query Label: {query_label}")
    print(f"Retrieved Labels: {retrieved_labels}")
    print(f"True Positives@K: {true_positives}")
    print(f"Total Retrieved@K: {k}")
    print(f"Total Relevant: {total_relevant}")
    print(f"P@K: {precision}, R@K: {recall}, F1@K: {f1}")

    return {
        "Precision@K": precision,
        "Recall@K": recall,
        "F1-Score@K": f1
    }


def main():
    st.title('CBIR - Búsqueda de imágenes por contenido')

    # Columnas de la interfaz
    col1, col2 = st.columns(2)

    with col1:
        st.header('QUERY')

        # Selección del extractor
        st.subheader('Choose feature extractor')
        option = st.selectbox('.', ('Color', 'Textura', 'Forma', 'CNN', 'SIFT'))

        # Seleccionar el monumento correcto
        st.subheader('Select the correct monument for the test image:')
        categories = train_df['Category'].unique().tolist()
        query_label = st.selectbox('Monument:', categories, key='test_monument')

        # Subir imagen
        st.subheader('Upload image')
        img_file = st.file_uploader(label='.', type=['png', 'jpg'])

        if img_file:
            img = Image.open(img_file)
            # Get a cropped image from the frontend
            cropped_img = st_cropper(img, realtime_update=True, box_color='#FF0004')

            # Manipulate cropped image at will
            st.write("Preview")
            _ = cropped_img.thumbnail((150, 150))
            st.image(cropped_img)

    with col2:
        st.header('RESULT')
        if img_file:
            st.markdown('**Retrieving .......**')
            start = time.time()

            retriev = retrieve_image(cropped_img, option, n_imgs=11)
            image_list = get_image_list()

            end = time.time()
            st.markdown('**Finish in ' + str(end - start) + ' seconds**')

            # Recuperar los índices de las imágenes más similares
            retrieved_indices = retrieve_image(cropped_img, option, n_imgs=11)
            image_list = get_image_list()

            # Usar los nombres de los archivos para obtener las etiquetas
            retrieved_labels = []
            for idx in retrieved_indices:
                image_name = image_list[idx]
                category = train_df.loc[train_df['Image Name'] == image_name, 'Category'].values
                if len(category) > 0:
                    retrieved_labels.append(category[0])
                else:
                    retrieved_labels.append("Unknown")

            # Calcular métricas
            metrics = calculate_metrics(query_label, retrieved_labels, 11)  # 11 = n_imgs

            # Mostrar métricas
            st.subheader('Métricas de evaluación:')
            st.write(metrics)

            col3, col4 = st.columns(2)

            with col3:
                image = Image.open(os.path.join(IMAGES_PATH, image_list[retriev[0]]))
                st.image(image, use_column_width='always')

            with col4:
                image = Image.open(os.path.join(IMAGES_PATH, image_list[retriev[1]]))
                st.image(image, use_column_width='always')

            col5, col6, col7 = st.columns(3)

            with col5:
                for u in range(2, 11, 3):
                    image = Image.open(os.path.join(IMAGES_PATH, image_list[retriev[u]]))
                    st.image(image, use_column_width='always')

            with col6:
                for u in range(3, 11, 3):
                    image = Image.open(os.path.join(IMAGES_PATH, image_list[retriev[u]]))
                    st.image(image, use_column_width='always')

            with col7:
                for u in range(4, 11, 3):
                    image = Image.open(os.path.join(IMAGES_PATH, image_list[retriev[u]]))
                    st.image(image, use_column_width='always')
            #try:
                # Recuperar las imágenes más similares
               # retriev = retrieve_image(img, option, n_imgs=11)
               # image_list = get_image_list()

               # end_time = time.time()
               # st.markdown(f'**Búsqueda completada en {end_time - start_time:.2f} segundos.**')

                # Mostrar las imágenes recuperadas
                #st.subheader('Imágenes similares:')
                #cols = st.columns(3)
                #for idx, retrieved_idx in enumerate(retriev):
                #    image_path = os.path.join(IMAGES_PATH, image_list[retrieved_idx])
                #    retrieved_image = Image.open(image_path)
                #    cols[idx % 3].image(retrieved_image, caption=f"Similitud #{idx + 1}", use_column_width=True)

            #except Exception as e:
                #st.error(f"Error durante la búsqueda: {e}")


if __name__ == '__main__':
    main()
