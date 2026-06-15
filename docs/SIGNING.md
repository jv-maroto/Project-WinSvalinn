# Firmar los instaladores (Azure Trusted Signing)

Firmar el `.exe`/`.msi` con un certificado Authenticode hace que **Windows SmartScreen
no avise** ("editor desconocido") y reduce los falsos positivos de antivirus.

La opción más barata y moderna es **Azure Trusted Signing** (~10 $/mes, plan Basic),
que además da **reputación de SmartScreen** sin esperar descargas.

## 1. Crear la cuenta en Azure (dónde ir)

1. Entra en **https://portal.azure.com** (necesitas una suscripción de Azure;
   sirve la de pago por uso).
2. Registra el proveedor: **Suscripciones → tu suscripción → Proveedores de recursos →**
   busca **`Microsoft.CodeSigning`** y pulsa **Registrar**.
3. En la barra de búsqueda del portal escribe **"Trusted Signing"** → **Crear** una
   cuenta de Trusted Signing. Elige región (p. ej. *West Europe* → endpoint
   `https://weu.codesigning.azure.net`).

## 2. Validar tu identidad y crear el perfil de certificado

4. Dentro de la cuenta de Trusted Signing → **Identity validations** → crea una.
   - **Particular (Individual):** Microsoft verifica tu identidad.
   - **Empresa (Organization):** documentación de la empresa.
   - *Puede tardar* (revisión manual de Microsoft).
5. Cuando esté **aprobada**, crea un **Certificate profile** de tipo **Public Trust**
   asociado a esa identidad. El **nombre del perfil** es `AZURE_TS_PROFILE`.
   El **nombre de la cuenta** es `AZURE_TS_ACCOUNT`.

## 3. Crear el "service principal" (para que GitHub pueda firmar)

6. **Microsoft Entra ID → Registros de aplicaciones → Nuevo registro** → crea una app.
   Anota **Directory (tenant) ID** (`AZURE_TENANT_ID`) y **Application (client) ID**
   (`AZURE_CLIENT_ID`). En **Certificados y secretos → Nuevo secreto de cliente** →
   copia el valor (`AZURE_CLIENT_SECRET`).
7. En la **cuenta de Trusted Signing → Control de acceso (IAM) → Agregar asignación de
   rol** → rol **"Trusted Signing Certificate Profile Signer"** → asígnaselo a esa app.

## 4. Poner los secretos en GitHub

En el repo: **Settings → Secrets and variables → Actions → New repository secret**,
crea estos 6:

| Secreto | Valor |
|---|---|
| `AZURE_TENANT_ID` | Directory (tenant) ID |
| `AZURE_CLIENT_ID` | Application (client) ID |
| `AZURE_CLIENT_SECRET` | el secreto de cliente |
| `AZURE_TS_ENDPOINT` | p. ej. `https://weu.codesigning.azure.net` |
| `AZURE_TS_ACCOUNT` | nombre de la cuenta de Trusted Signing |
| `AZURE_TS_PROFILE` | nombre del perfil de certificado |

## 5. Firmar un release

**Actions → "Sign release (Azure Trusted Signing)" → Run workflow →** escribe el tag
(p. ej. `v1.0.0`). Descarga los instaladores del release, los firma y los vuelve a
subir ya firmados. A partir de ahí, SmartScreen deja de avisar.

> El workflow está en `.github/workflows/sign.yml`. Si los secretos no están puestos,
> falla con un aviso claro en vez de hacer nada raro.
