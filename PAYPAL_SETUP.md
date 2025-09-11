# Configuración de PayPal para Ebooks

## Variables de Entorno Requeridas

Para integrar PayPal como método de pago para ebooks, necesitas configurar las siguientes variables de entorno:

### Variables Obligatorias

```bash
# PayPal API Credentials
PAYPAL_CLIENT_ID=tu_client_id_aqui
PAYPAL_CLIENT_SECRET=tu_client_secret_aqui
PAYPAL_MODE=sandbox  # o "live" para producción

# Base URL de tu aplicación (ya existente)
BASE_URL=https://tu-dominio.com  # o http://localhost:8000 para desarrollo
```

## Cómo Obtener las Credenciales de PayPal

### 1. Crear una Aplicación en PayPal Developer

1. Ve a [PayPal Developer Dashboard](https://developer.paypal.com/)
2. Inicia sesión con tu cuenta de PayPal
3. Haz clic en "Create App"
4. Completa la información:
   - **App Name**: Nombre de tu aplicación
   - **Merchant**: Selecciona tu cuenta de merchant
   - **Features**: Marca "Accept payments"
   - **Products**: Selecciona "Checkout"

### 2. Configurar Sandbox (Desarrollo)

Para desarrollo, usa el modo **Sandbox**:

```bash
PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=tu_sandbox_client_id
PAYPAL_CLIENT_SECRET=tu_sandbox_client_secret
```

- Las credenciales de sandbox están en la sección "Sandbox" de tu app
- Puedes crear cuentas de prueba en [PayPal Sandbox](https://developer.paypal.com/developer/accounts/)

### 3. Configurar Live (Producción)

Para producción, usa el modo **Live**:

```bash
PAYPAL_MODE=live
PAYPAL_CLIENT_ID=tu_live_client_id
PAYPAL_CLIENT_SECRET=tu_live_client_secret
```

- Las credenciales de live están en la sección "Live" de tu app
- Solo disponible después de que PayPal apruebe tu aplicación

## Configuración de Webhooks (Opcional pero Recomendado)

Para recibir notificaciones automáticas de pagos completados:

1. En tu app de PayPal Developer, ve a "Webhooks"
2. Agrega una nueva URL de webhook: `https://tu-dominio.com/webhooks/paypal`
3. Selecciona los eventos:
   - `CHECKOUT.ORDER.APPROVED`
   - `PAYMENT.CAPTURE.COMPLETED`

## URLs de Retorno

El sistema está configurado para usar estas URLs automáticamente:

- **Success**: `{BASE_URL}/paypal/pago-exitoso`
- **Cancel**: `{BASE_URL}/ebooks/{ebook_id}?compra=cancelada`
- **Webhook**: `{BASE_URL}/webhooks/paypal`

## Ejemplo de Archivo .env

```bash
# Configuración existente
DATABASE_URL=postgresql://...
GMAIL_TOKEN=...
ADMIN_EMAIL=...
BASE_URL=...

# Nueva configuración PayPal
PAYPAL_CLIENT_ID=AeHGxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
PAYPAL_CLIENT_SECRET=ELTxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
PAYPAL_MODE=sandbox
```

## Flujo de Pago

1. Usuario hace clic en "Pagar con PayPal"
2. Se crea una orden en PayPal (`/paypal/crear-orden`)
3. Usuario es redirigido a PayPal para aprobar el pago
4. PayPal redirige de vuelta a `/paypal/pago-exitoso`
5. Se captura el pago y se confirma la compra
6. Se envían emails de confirmación
7. Usuario puede descargar el ebook

## Monedas Soportadas

El sistema está configurado para usar **USD** como moneda para los ebooks, que es compatible con PayPal internacional.

## Seguridad

- Las credenciales de PayPal nunca se exponen al frontend
- Todas las transacciones se validan en el servidor
- Los tokens de acceso se generan dinámicamente para cada operación

## Testing

Para probar la integración:

1. Configura las variables de entorno con credenciales de sandbox
2. Usa cuentas de prueba de PayPal Sandbox
3. Realiza compras de prueba para verificar el flujo completo

## Troubleshooting

### Error: "Error obteniendo token de PayPal"
- Verifica que `PAYPAL_CLIENT_ID` y `PAYPAL_CLIENT_SECRET` sean correctos
- Asegúrate de que `PAYPAL_MODE` sea "sandbox" o "live"

### Error: "Error al crear orden en PayPal"
- Verifica que tu aplicación tenga permisos para "Checkout"
- Revisa que el precio del ebook sea mayor a 0

### Webhook no funciona
- Verifica que la URL del webhook sea accesible públicamente
- Asegúrate de que `BASE_URL` esté configurado correctamente
