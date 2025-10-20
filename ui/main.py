import gradio as gr
import requests
import time
import json
from typing import IO
import pandas as pd
import os
 
base_system_prompt = "You are an assistant that creates compelling product descriptions. You will be given a product name and its specs, and your task is to write a creative selling text for the product page of an online store. The text should be ready to insert directly into the description, without your personal comments like \"Here is the product description.\" The text must contain ONLY A BRIEF PRODUCT DESCRIPTION AND NOTHING ELSE. The description should be no longer than 3-5 sentences."
 
df = None
filename = "data.xlsx"

# = Отправка файла ===================================================================
def send_file(file, system_prompt):
    with open(file.name, "rb") as f:
        files = {"file": (file.name, f, "multipart/form-data")}
        data = {"generation": json.dumps({"system":system_prompt})}
        backend_url = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")
        response = requests.post(f"{backend_url}/upload", data=data, files=files)
    
    job_id = response.json()["job_id"]
    total = response.json()["submitted"]
    completed = 0

    while completed < total:
        status = requests.get(f"{backend_url}/status/{job_id}").json()
        completed = status["completed"]
        progress = completed / total
        # print(status)
        yield join_cards(status["results_preview"]), f"Progress: {completed}/{total} ({progress*100:.1f}%)", status
        time.sleep(2)

    df['generated_text'] = ''
    for row in status["results_preview"].values():
        row_data = row['data']
        df.loc[df['id'] == row_data['id'], 'generated_text'] = row['generated_text']
    
    return response.json(), "✅ All tasks completed!", status

# = Загрузка Excel в датафрейм на фронтенд ===========================================
def load_excel_to_dataframe(file_obj: IO) -> pd.DataFrame:
    global df, filename
    
    if file_obj is None:
        return pd.DataFrame()
        
    try:
        df = pd.read_excel(file_obj.name)
        filename = file_obj.name
        return df
    except Exception as e:
        gr.Warning(f"Error reading the Excel file: {e}")
        return pd.DataFrame()

def save_to_excel():
    df.to_excel(filename, index=False)
    return filename

# = Конструктор Frontend =============================================================
with gr.Blocks() as demo:
    gr.Markdown("## 🧠 Результаты в карточках")
    
    gr.Markdown("### 1️⃣ Загрузите файл")
    input_file = gr.File(label="Загрузите файл", height=100)  
    dataframe = gr.DataFrame(
        label="Данные из файла",
        interactive=False,
        max_height=250
    )
    
    with gr.Row():
        with gr.Column():  
            gr.Markdown("### 2️⃣ Отредактируйте промпт")                
            system_prompt = gr.TextArea(base_system_prompt)             
            submit = gr.Button("Отправить")
            gr.Markdown("### 4️⃣ Сохраните новый файл\nВ загруженный файл будет добавлен новый столбец со сгенерированными данными\n\n❗При перезагрузке страницы все данные будут утеряны❗")
            save = gr.Button("Сохранить")
            savefile = gr.File(label="Скачать Excel (нажмите на текст, указывающий на размер файла)", height=30)
        with gr.Column():
            gr.Markdown("### 3️⃣ Результат генерации появится здесь")
            logs = gr.Text(label = "Логи", interactive=False)
            output_html = gr.HTML()
            # result_json = gr.JSON()

    submit.click(send_file, inputs=[input_file, system_prompt], outputs=[output_html, logs])
    input_file.upload(
        fn=load_excel_to_dataframe,
        inputs=input_file,
        outputs=dataframe
    )
    save.click(save_to_excel, inputs=[], outputs=savefile)

# ========================================================================
# = ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==============================================
# ========================================================================

def join_cards(results):
    cards_html = "".join(
        [f"<div style='border:1px solid #ccc; padding:10px; margin-bottom:5px; border-radius:8px;'>"
         f"<b>{r['data']['product_name']}:</b> {r['generated_text']}</div>"
         for id, r in results.items()]
    )
    return cards_html

if __name__ == "__main__":
    # Allow overriding host/port via environment variables when running in Docker
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name=host, server_port=port)
