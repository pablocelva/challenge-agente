# BimBamIA - Asistente Virtual de Atención al Cliente

## Descripción General

BimBamIA es un agente de inteligencia artificial diseñado para brindar atención al cliente automatizada para **BimBam Buy**, una plataforma de e-commerce. El agente utiliza Retrieval-Augmented Generation (RAG) para responder preguntas basándose en la documentación oficial de la empresa, cubriendo temas como devoluciones, envíos, pagos, garantías y programa de afiliados.

## Links Demo
- Streamlit: 
- Video: 

## Arquitectura

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Streamlit  │────▶│  LangGraph   │───▶│   Cohere    │
│  (Frontend) │     │ (Orquestador)│     │  (LLM + Emb)│
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                    ┌──────▼───────┐
                    │  ChromaDB    │
                    │  (Vector DB) │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   SQLite     │
                    │  (Checkpoint)│
                    └──────────────┘
```

### Flujo del Agente

1. **Clasificación de intención**: El agente analiza la pregunta y determina si requiere búsqueda documental (`DOCUMENT`) o es una respuesta general (`GENERAL`).
2. **Recuperación de documentos**: Si es DOCUMENT, busca los chunks más relevantes en ChromaDB.
3. **Generación de respuesta**: Utiliza el contexto recuperado para generar una respuesta precisa con Cohere.
4. **Formateo**: Presenta la respuesta de forma clara y profesional al usuario.

## Tecnologías

| Componente | Tecnología | Versión |
|------------|-----------|---------|
| LLM | Cohere Command A | 03-2025 |
| Embeddings | Cohere Embed v4.0 | - |
| Framework de Agentes | LangGraph | Latest |
| Cadena de LangChain | LangChain | Latest |
| Base de datos vectorial | ChromaDB | Latest |
| Frontend | Streamlit | Latest |
| Persistencia | SQLite (SqliteSaver) | - |
| Lenguaje | Python | 3.12+ |

## Estructura del Proyecto

```
bimbam-ia-agente/
├── app.py                  # Interfaz Streamlit
├── config.py               # Configuración centralizada
├── requirements.txt        # Dependencias
├── .env.example            # Variables de entorno (ejemplo)
├── graph/
│   ├── __init__.py
│   ├── builder.py          # Construcción del grafo LangGraph
│   ├── state.py            # Definición del estado del agente
│   ├── nodes.py            # Nodos del grafo
│   └── edges.py            # Condicionales de routing
├── agents/
│   ├── __init__.py
│   ├── document_agent.py   # Agente de respuesta documental
│   └── prompts.py          # Prompts del sistema
├── rag/
│   ├── __init__.py
│   ├── loader.py           # Carga y splitting de PDFs
│   ├── embeddings.py       # Configuración de Cohere Embed
│   └── vectorstore.py      # Creación del ChromaDB
├── tools/
│   ├── __init__.py
│   └── search_tools.py     # Herramienta de búsqueda
└── docs/
    ├── reembolsos-devoluciones.pdf
    ├── programa-afiliados.pdf
    ├── guia-envios.pdf
    ├── faq-metodos-pago.pdf
    └── manual-garantia.pdf
```

## Instalación

### Prerrequisitos

- Python 3.12 o superior
- API Key de Cohere
- Git

### Pasos

1. Clonar el repositorio:
```bash
git clone https://github.com/pablocelva/bimbam-ia-agente.git
cd bimbam-ia-agente
```

2. Crear entorno virtual:
```bash
python -m venv venv
source venv/Scripts/activate     # Windows
source venv/bin/activate         # Linux/Mac
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
```bash
cp .env.example .env
```
Editar `.env` y agregar tu API key:
```
COHERE_API_KEY=tu-api-key-aqui
```

5. Ejecutar la aplicación:
```bash
streamlit run app.py
```

## Ejemplos de Preguntas

| Categoría | Pregunta |
|-----------|----------|
| Devoluciones | ¿Cuál es el plazo para devolver un producto? |
| Devoluciones | ¿Puedo cambiar un producto sin abrirlo? |
| Devoluciones | ¿Cuánto tarda en llegar mi reembolso? |
| Envíos | ¿Cuánto cuesta el envío y cuánto tarda? |
| Pagos | ¿Qué métodos de pago aceptan? |
| Garantía | ¿Cómo reclamo la garantía de un producto? |
| Afiliados | ¿Cómo funciona el programa de afiliados? |
| Afiliados | ¿Cómo me afilio a BimBam Buy? |

## Ejemplo de Respuesta

**Pregunta:** ¿Cuál es el plazo para devolver un producto?

**Respuesta del agente:**
```
En BimBam Buy, entendemos que a veces es necesario devolver un producto, y queremos hacer que el proceso sea lo más sencillo posible para ti. Aquí te explicamos los plazos y condiciones para solicitar una devolución:

Plazos para solicitar devolución:

Retracto de compra (cambio de opinión): Tienes 10 días corridos después de recibir tu pedido para solicitar una devolución, siempre que el producto cumpla con los requisitos de elegibilidad.

Producto incorrecto, faltante o dañado visible: Debes ingresar tu solicitud dentro de las 48 horas posteriores a la entrega, adjuntando evidencia fotográfica o video según el tipo de incidencia.

Falla de funcionamiento: La solicitud debe realizarse dentro del período de garantía aplicable al producto, conforme al Manual de Garantía de Productos de BimBam Buy.

Condiciones para aceptar una devolución:

Contar con comprobante de compra o número de orden.
Presentarse dentro del plazo aplicable.
El producto debe estar completo, con accesorios, manuales y obsequios promocionales si los hubiera.
Proceso de reembolso:

Una vez aprobada la devolución, el reembolso se procesa en un plazo de entre 5 y 10 días hábiles, dependiendo del método de pago y del país de origen de la compra.

Canales de atención:

Puedes gestionar tu solicitud de devolución a través de nuestros canales oficiales:

Centro de ayuda en la web
Formulario de postventa
Chat de soporte
Correo de atención al cliente

Importante:

En situaciones que requieran validación adicional, como análisis técnico o verificación de pago, el plazo de respuesta puede extenderse. Te mantendremos informado sobre el estado de tu solicitud y el nuevo tiempo estimado.

Si tienes alguna duda o necesitas más información, no dudes en contactarnos a través de nuestros canales oficiales. ¡Estamos aquí para ayudarte!

Resumen de plazos:

Retracto de compra: 10 días corridos
Producto incorrecto/dañado: 48 horas
Falla de funcionamiento: período de garantía

¡Gracias por confiar en BimBam Buy!
```

## Deploy

La aplicación está desplegada en **Streamlit Cloud**.

### Notas sobre el deploy

- Streamlit Cloud pausa la app después de 12 horas de inactividad
- El ChromaDB se reconstruye automáticamente al iniciar (~20-30 segundos)
- SQLite es efímero en Streamlit Cloud (se reinicia con cada deploy)


## Licencia

Proyecto desarrollado para el Challenge de Alura Latam.