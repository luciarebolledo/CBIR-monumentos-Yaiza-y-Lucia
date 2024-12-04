import os
import shutil

# Directorio principal que contiene las subcarpetas
root_dir = "dataset"  # Cambia "dataset" por la ruta a tu directorio principal
train_dir = os.path.join(root_dir, "train")

# Crear la carpeta 'train' si no existe
os.makedirs(train_dir, exist_ok=True)

# Iterar por las subcarpetas
for subfolder in os.listdir(root_dir):
    subfolder_path = os.path.join(root_dir, subfolder)

    # Verificar que sea una carpeta y no la carpeta "train"
    if os.path.isdir(subfolder_path) and subfolder != "train":
        for file in os.listdir(subfolder_path):
            file_path = os.path.join(subfolder_path, file)

            # Verificar que sea un archivo (imagen)
            if os.path.isfile(file_path):
                # Crear un nuevo nombre para el archivo basado en la carpeta
                base_name, ext = os.path.splitext(file)  # Separar nombre y extensión
                new_file_name = f"{subfolder}_{base_name}{ext}"
                new_file_path = os.path.join(train_dir, new_file_name)

                # Asegurarse de que el nombre sea único
                counter = 1
                while os.path.exists(new_file_path):
                    new_file_name = f"{subfolder}_{base_name}_{counter}{ext}"
                    new_file_path = os.path.join(train_dir, new_file_name)
                    counter += 1

                # Mover y renombrar el archivo
                shutil.copy(file_path, new_file_path)

print("¡Todas las imágenes han sido movidas y renombradas en la carpeta 'train'!")
