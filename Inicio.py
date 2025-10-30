import os
import streamlit as st
import base64
from openai import OpenAI
# import openai # Eliminado ya que usamos el cliente
from PIL import Image, ImageOps
import numpy as np
import pandas as pd
from streamlit_drawable_canvas import st_canvas

# --- Estilos CSS Personalizados ---
st.markdown("""
<style>
    /* Layout centrado */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 720px;
    }
    /* Títulos centrados */
    h1, h2, h3 {
        text-align: center;
    }
    /* Contenedor de sección (tarjeta) */
    .section-container {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 25px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.04);
        border: 1px solid #e6e6e6;
        margin-bottom: 20px;
    }
    /* Estilo del lienzo */
    [key="canvas"] {
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    /* Botón principal (verde fruta) */
    .stButton>button:first-of-type {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        width: 100%;
    }
    .stButton>button:first-of-type:hover {
        background-color: #45a049;
        box-shadow: 0 6px 15px rgba(0,0,0,0.15);
    }
    /* Botón de historia (naranja) */
    .stButton:has(button > span:contains('Crear historia')) > button {
        background-color: #FF9800;
    }
    .stButton:has(button > span:contains('Crear historia')) > button:hover {
        background-color: #FB8C00;
    }
    /* Caja de respuesta (análisis) */
    .response-box {
        background-color: #f0fdf4; /* Verde claro */
        border: 1px solid #bbf7d0;
        border-radius: 8px;
        padding: 15px;
        color: #166534; /* Verde oscuro */
        margin-top: 15px;
        line-height: 1.6;
    }
    /* Caja de respuesta (historia) */
    .story-box {
        background-color: #fffbeb; /* Amarillo claro */
        border: 1px solid #fef3c7;
        border-radius: 8px;
        padding: 15px;
        color: #78350f; /* Marrón */
        margin-top: 15px;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# Variables de la app (como en tu código original)
Expert=" "
profile_imgenh=" "

# --- Inicializar session_state ---
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'full_response' not in st.session_state:
    st.session_state.full_response = ""
if 'base64_image' not in st.session_state:
    st.session_state.base64_image = ""
    
# --- Función de codificación ---
def encode_image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
            return encoded_image
    except FileNotFoundError:
        return "Error: La imagen no se encontró en la ruta especificada."


# --- Interfaz de la App ---
st.set_page_config(page_title='Analizador de Frutas')
st.title('Analizador de Frutas 🍓 Creador de Historias')
st.subheader("Dibuja una fruta en el lienzo y presiona 'Analizar'")

# --- Sección 1: Clave de API ---
client = None
with st.container():
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.markdown("### 🔑 Paso 1: Ingresa tu Clave de OpenAI")
    ke = st.text_input('Tu clave aquí:', type="password", label_visibility="collapsed", placeholder="sk-...")
    
    if not ke:
        st.info("Por favor ingresa tu clave de API de OpenAI para continuar.")
    else:
        os.environ['OPENAI_API_KEY'] = ke
        api_key = ke
        # CORRECCIÓN: Inicializar el cliente aquí
        client = OpenAI(api_key=api_key)
        st.success("¡Clave de API cargada! 🍎")
    st.markdown('</div>', unsafe_allow_html=True)


# --- Sección 2: Lienzo de Dibujo (solo si hay clave) ---
if client:
    with st.container():
        st.markdown('<div class="section-container">', unsafe_allow_html=True)
        st.markdown("### 🎨 Paso 2: Dibuja una Fruta")

        col1, col2 = st.columns([1, 2])
        with col1:
            stroke_width = st.slider('Ancho de línea:', 1, 30, 5)
            # AÑADIDO: Selector de color del trazo
            stroke_color = st.color_picker('Color del trazo:', '#000000')
            st.info("¡Intenta dibujar una manzana, banana, naranja, etc.!")
            analyze_button = st.button("Analizar Dibujo 🍏", use_container_width=True)

        with col2:
            canvas_result = st_canvas(
                stroke_width=stroke_width,
                # ACTUALIZADO: Color del trazo dinámico
                stroke_color=stroke_color,
                background_color='#FFFFFF', # Fondo blanco
                height=300,
                width=400,
                drawing_mode="freedraw",
                key="canvas",
            )
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Lógica de Análisis ---
    if canvas_result.image_data is not None and analyze_button:
        with st.spinner("Pensando qué fruta es... 🫐"):
            # Guardar y codificar la imagen
            input_numpy_array = np.array(canvas_result.image_data)
            input_image = Image.fromarray(input_numpy_array.astype('uint8')).convert('RGBA')
            input_image.save('img.png')
            
            base64_image = encode_image_to_base64("img.png")
            st.session_state.base64_image = base64_image
                
            # CAMBIO DE TEMA: Prompt de Fruta
            prompt_text = (f"Identifica qué fruta es esta. Describe el dibujo brevemente en español. Si no parece una fruta, di que no puedes identificarla.")
        
            try:
                # CORRECCIÓN: Usar 'client.chat.completions.create'
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt_text},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{base64_image}",
                                    },
                                },
                            ],
                        }
                    ],
                    max_tokens=500,
                )
                
                full_response = ""
                if response.choices[0].message.content is not None:
                    full_response = response.choices[0].message.content
                
                st.markdown("### 🍇 Análisis del Dibujo:")
                st.markdown(f"<div class='response-box'>{full_response}</div>", unsafe_allow_html=True)
                
                # Guardar en session_state
                st.session_state.full_response = full_response
                st.session_state.analysis_done = True
                
                if Expert== profile_imgenh:
                    st.session_state.mi_respuesta= response.choices[0].message.content
        
            except Exception as e:
                st.error(f"Ocurrió un error: {e}")

    # --- Sección 3: Crear Historia (si el análisis está hecho) ---
    if st.session_state.analysis_done:
        with st.container():
            st.markdown('<div class="section-container">', unsafe_allow_html=True)
            st.markdown("### 📚 Paso 3: ¿Creamos una historia?")
            st.write(f"¡Genial! Ahora podemos crear una historia sobre tu dibujo.")
            
            if st.button("✨ Crear historia infantil 🍉", use_container_width=True):
                with st.spinner("Escribiendo una historia... 🍌"):
                    
                    # CAMBIO DE TEMA: Story Prompt
                    story_prompt = f"Basándote en esta descripción de un dibujo de una fruta: '{st.session_state.full_response}', crea una historia infantil breve y entretenida sobre esa fruta. La historia debe ser creativa y apropiada para niños."
                    
                    # CORRECCIÓN: Usar 'client.chat.completions.create'
                    story_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": story_prompt}],
                        max_tokens=500,
                    )
                    
                    st.markdown("### 📖 ¡Tu Cuento de Frutas!")
                    story_content = story_response.choices[0].message.content
                    st.markdown(f"<div class='story-box'>{story_content}</div>", unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

# --- "Acerca de" (movido del sidebar) ---
with st.expander("ℹ️ Acerca de esta App"):
    st.write("En esta aplicación usamos IA (GPT-4o-mini) para interpretar tus dibujos de frutas y convertirlos en descripciones e historias.")
