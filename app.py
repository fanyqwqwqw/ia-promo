from flask import Flask, jsonify, request
from flasgger import Swagger
import pandas as pd
from sklearn.cluster import KMeans

app = Flask(__name__)

# Crear la instancia de Swagger y cargar el archivo YAML
swagger = Swagger(app, template_file='swagger.yaml')

# Cargar y procesar el CSV
def process_csv(csv_file):
    df = pd.read_csv(csv_file)
    
    # Filtrar y preparar los datos para el clustering
    features = df[['ProductoPrecio', 'ProductoStock', 'TotalPedido', 'Cantidad']]
    
    # KMeans para seleccionar productos para la promoción (clusters)
    kmeans = KMeans(n_clusters=3, random_state=0)
    df['Cluster'] = kmeans.fit_predict(features)
    
    # Seleccionar productos de los clusters para la promoción
    selected_products = df.groupby('Cluster').agg({
        'ProductoNombre': 'first'  # Tomar el primer producto de cada cluster
    }).reset_index()
    
    # Extraer los nombres de los productos seleccionados
    return selected_products['ProductoNombre'].tolist()

# Ruta para recibir el archivo CSV y devolver los productos seleccionados
@app.route('/api/promocion', methods=['POST'])
def promocion():
    file = request.files['file']
    if file and file.filename.endswith('.csv'):
        products = process_csv(file)
        return jsonify({"productos": products}), 200
    return jsonify({"error": "Archivo no válido. Asegúrese de que el archivo sea un CSV."}), 400

if __name__ == '__main__':
    app.run(debug=True)
