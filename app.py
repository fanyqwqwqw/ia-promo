from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from flasgger import Swagger

app = Flask(__name__)
swagger = Swagger(app)

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    """
    Upload CSV and return products for promotion
    ---
    tags:
      - Promotion API
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: CSV file with product data
    responses:
      200:
        description: List of products selected for promotion
        schema:
          type: array
          items:
            type: string
    """
    try:
        # Load the CSV file
        file = request.files['file']
        df = pd.read_csv(file)

        # Ensure necessary columns are present
        required_columns = [
            'Id', 'Nombre', 'Descripcion', 'Precio', 'CostoUnitario', 
            'VentasHistoricas', 'FechaUltimaVenta', 'Stock', 'DescuentoMaxPermitido', 
            'MargenGanancia', 'IdCategoria']
        if not all(col in df.columns for col in required_columns):
            return jsonify({"error": "Missing required columns in the CSV."}), 400

        # Feature engineering for promotion criteria
        df['TiempoSinVenta'] = (pd.Timestamp.now() - pd.to_datetime(df['FechaUltimaVenta'])).dt.days
        df['PromocionRecomendada'] = (df['VentasHistoricas'] < 400) & \
                                      (df['TiempoSinVenta'] > 15) & \
                                      (df['MargenGanancia'] > df['DescuentoMaxPermitido']) & \
                                      (df['Stock'] > 10)

        # Train a simple classifier to refine promotions
        features = ['VentasHistoricas', 'TiempoSinVenta', 'MargenGanancia', 'DescuentoMaxPermitido', 'Stock']
        X = df[features]
        y = df['PromocionRecomendada'].astype(int)

        # Handle potential issues with nulls
        X.fillna(0, inplace=True)

        model = RandomForestClassifier(random_state=42)
        model.fit(X, y)
        df['PredictedPromotion'] = model.predict(X)

        # Select products for promotion
        promotion_products = df[df['PredictedPromotion'] == 1]

        # Ensure there are 4 products with different IdCategoria
        selected_products = []
        selected_categories = set()

        for index, row in promotion_products.iterrows():
            if len(selected_categories) < 4:
                if row['IdCategoria'] not in selected_categories:
                    selected_products.append(row['Nombre'])
                    selected_categories.add(row['IdCategoria'])

        return jsonify(selected_products), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
