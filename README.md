# Taller - Streaming (MDD)
### Realizado por: Gustavo Jerez

## Estructura del repositorio

```
lab3-streaming-MDD/
├── data/                       # JSON de prueba
├── ec2-python-polars/          # Infraestructura Terraform EC2 + Python + Polars
├── emr-cluster/                # Infraestructura Terraform Cluster EMR 
├── scripts/                    # Script para generación de JSON de prueba 
├── src/                        # Scripts con implementación de las tareas
├── tests/                      # Scripts de tests de validación de las tareas
├── .gitignore
└── README.md
```

## Cómo ejecutar los tests

### Ambiente local
Se asume que se cuenta con un ambiente python >=3.12, y las librerias estandar más las necesarias para el taller: pyspark, pytest. Igualmente se debe instalar el paquete para aplicar Bloom filter en la tarea 4 si aún no se tiene: `pip install bloom_filter2`.

Para aplicar los tests se debe estar ubicado en la raiz del repo y apuntar al test deseado usando el comando:
```bash
pytest tests/test_task_1.py    
```

### AWS 
Se asume que se cuenta con el agente SSM previamente instalado, asi como AWS CLI y Terraform. Se puede validar con los siguientes comandos:

```bash
terraform -version
aws sts get-caller-identity        
```

En este caso, se debe acceder a las carpetas respectivas de las tareas 5 y 6 y seguir las instrucciones del README correspondiente.