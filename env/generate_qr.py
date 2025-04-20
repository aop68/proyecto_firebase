import qrcode
import os
import requests

# Obtener la IP pública
def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org')
        return response.text
    except:
        return None

# Obtener la IP pública
public_ip = get_public_ip()
if public_ip:
    # URL de la aplicación usando la IP pública
    app_url = f"http://{public_ip}"

    # Crear el código QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(app_url)
    qr.make(fit=True)

    # Crear la imagen
    img = qr.make_image(fill_color="black", back_color="white")

    # Asegurarse de que el directorio existe
    os.makedirs("static/images", exist_ok=True)

    # Guardar la imagen
    img.save("static/images/app_qr.png")

    print(f"Código QR generado y guardado en static/images/app_qr.png")
    print(f"URL pública de la aplicación: {app_url}")

    print("\nIMPORTANTE:")
    print("1. La aplicación debe estar ejecutándose para que el código QR funcione")
    print("2. Asegúrate de haber configurado el port forwarding en tu router")
    print("3. El firewall de Windows debe permitir conexiones al puerto 80")
else:
    print("No se pudo obtener la IP pública. Verifica tu conexión a internet.") 