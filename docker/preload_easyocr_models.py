import os

import easyocr


model_directory = os.environ[
    "EASYOCR_MODEL_STORAGE_DIRECTORY"
]
user_network_directory = os.environ[
    "EASYOCR_USER_NETWORK_DIRECTORY"
]

reader = easyocr.Reader(
    ["bg", "en"],
    gpu=False,
    model_storage_directory=model_directory,
    user_network_directory=user_network_directory,
    download_enabled=True,
)

assert reader is not None
print("EasyOCR bg/en models preloaded")
