import os
import pandas as pd

# Rutas a las carpetas de imágenes
train_dir = "train"

# Crear etiquetas basadas en los prefijos de los nombres de las imágenes
def assign_label(image_name):
    # Buscar coincidencias exactas con los prefijos esperados
    if image_name.startswith("taj_mahal_"):
        return "Taj Mahal"
    elif image_name.startswith("burj_kalifa_"):
        return "Burj Khalifa"
    elif image_name.startswith("eiffel_tower_"):
        return "Eiffel Tower"
    elif image_name.startswith("pyramids_of_giza_"):
        return "Pyramids of Giza"
    elif image_name.startswith("colosseum_"):
        return "Colosseum"

def create_csv_for_directory(directory, output_filename):
    # Verificar si el directorio existe
    if not os.path.exists(directory):
        print(f"El directorio {directory} no existe.")
        return

    # Listar todos los archivos en el directorio que sean imágenes
    image_names = [f for f in os.listdir(directory) if f.lower().endswith(('jpg', 'jpeg', 'png'))]

    # Crear listas para el índice y las etiquetas # Asignar índices del 1 al número de imágenes
    categories = [assign_label(name) for name in image_names]  # Generar categorías basadas en los nombres

    # Crear el DataFrame
    df = pd.DataFrame({
        'Image Name': image_names,
        'Category': categories
    })

    # Guardar el DataFrame en un archivo CSV
    output_path = os.path.join(directory, output_filename)
    df.to_csv(output_path, index=False)

    # Imprimir el DataFrame para verificar
    print(f"Dataset guardado en: {output_path}")
    print(df)

# Crear CSV para el directorio de entrenamiento
create_csv_for_directory(train_dir, 'image_dataset_with_labels_train.csv')
