import requests
import json
import uuid
import boto3

def lambda_handler(event, context):
    # URL de la API de sismos
    url = "https://ultimosismo.igp.gob.pe/api/ultimo-sismo/ajaxb/2024"

    # Encabezados para evitar bloqueos
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }

    try:
        # Realizar la solicitud a la API
        response = requests.get(url, headers=headers)
        
        # Verificar el código de estado de la respuesta
        if response.status_code != 200:
            return {
                'statusCode': response.status_code,
                'body': 'Error al acceder a la API'
            }

        # Procesar la respuesta JSON
        data = response.json()

        # Obtener los últimos 10 sismos
        ultimos_10_sismos = data[-10:]

        # Crear una lista para almacenar los datos procesados
        rows = []

        # Extraer datos relevantes de cada sismo
        for sismo in ultimos_10_sismos:
            sismo_data = {
                'id': str(uuid.uuid4()),  # Generar un ID único
                'codigo': sismo.get('codigo', ''),
                'fecha_local': sismo.get('fecha_local', ''),
                'hora_local': sismo.get('hora_local', ''),
                'latitud': sismo.get('latitud', ''),
                'longitud': sismo.get('longitud', ''),
                'magnitud': sismo.get('magnitud', ''),
                'profundidad': sismo.get('profundidad', ''),
                'referencia': sismo.get('referencia', ''),
                'intensidad': sismo.get('intensidad', ''),
                'reporte_acelerometrico_pdf': sismo.get('reporte_acelerometrico_pdf', '')
            }
            rows.append(sismo_data)

        # Conectar a DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('Sismos')

        # Eliminar todos los elementos existentes en la tabla
        scan = table.scan()
        with table.batch_writer() as batch:
            for each in scan.get('Items', []):
                batch.delete_item(Key={'id': each['id']})

        # Insertar los últimos 10 sismos en la tabla
        with table.batch_writer() as batch:
            for row in rows:
                batch.put_item(Item=row)

        # Retornar los datos procesados directamente
        return {
            'statusCode': 200,
            'body': rows,
            'headers': {
                'Content-Type': 'application/json'
            }
        }

    except Exception as e:
        # Manejar excepciones y retornar el error
        return {
            'statusCode': 500,
            'body': {'error': str(e)},
            'headers': {
                'Content-Type': 'application/json'
            }
        }
