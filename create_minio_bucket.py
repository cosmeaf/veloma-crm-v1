#!/usr/bin/env python3
import os
from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações
MINIO_ENDPOINT   = os.getenv("MINIO_ENDPOINT", "localhost:9002")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin-alvelos")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "alvelos2025")
MINIO_BUCKET     = os.getenv("MINIO_BUCKET", "finance-app")
MINIO_SECURE     = os.getenv("MINIO_SECURE", "false").lower() == "true"

def main():
    print(f"DEBUG: Endpoint: {MINIO_ENDPOINT}")
    print(f"DEBUG: Access Key: {MINIO_ACCESS_KEY}")
    print(f"DEBUG: Secure: {MINIO_SECURE}")
    print(f"DEBUG: Bucket: {MINIO_BUCKET}")

    # Inicializa o cliente MinIO
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE,
        region="us-east-1",
    )

    try:
        # Verifica se o bucket existe
        found = client.bucket_exists(MINIO_BUCKET)
        print(f"DEBUG: Bucket exists: {found}")
        if not found:
            client.make_bucket(MINIO_BUCKET)
            print(f"✅ Bucket '{MINIO_BUCKET}' criado com sucesso.")
        else:
            print(f"ℹ️ Bucket '{MINIO_BUCKET}' já existe.")
            # Verifica permissões no bucket
            try:
                client.get_bucket_policy(MINIO_BUCKET)
                print(f"✅ Usuário tem acesso ao bucket '{MINIO_BUCKET}'.")
            except S3Error as e:
                print(f"⚠️ Usuário não tem acesso ao bucket '{MINIO_BUCKET}': {e}")
    except S3Error as e:
        print(f"❌ Erro ao criar bucket: {e}")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    main()