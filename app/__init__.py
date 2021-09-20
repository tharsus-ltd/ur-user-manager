import os

__version__ = '0.0.1'
__service__ = os.environ.get("SERVICE_NAME", "User Manager")
__root__ = os.environ.get("ROOT_PATH", "/")

__secret_key__ = os.environ.get("SECRET_KEY", "e9629f658c37859ab9d74680a3480b99265c7d4c89224280cb44a255c320661f")
