import os
import json
import uuid
import tarfile
import re
import shutil
import docx
import sys
import time
import unicodedata
import random
import requests
import random
import string
from datetime import datetime
from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import shutil
from flask_cors import CORS

app = Flask(__name__)
# Configuração do CORS para permitir o domínio específico
CORS(app, resources={r"/*": {"origins": "*"}})


# Carrega as variáveis do arquivo .env
load_dotenv()
# Acessar a variável de ambiente
API_URL = os.getenv("API_URL", "https://presence.ipgc.org.br") 

#=====================Criando JSONS=====================================================


def limpar_pastas(*pastas):
    for pasta in pastas:
        if os.path.exists(pasta):
            shutil.rmtree(pasta) 
        os.makedirs(pasta, exist_ok=True) 


def processar_documento(docx_path, output_folder):
    doc = docx.Document(docx_path)
 
 #palavras que vao identificar cada unidade
    UNIT_KEYWORDS = [
        "CONTEXTUALIZANDO",
        "CONECTANDO",
        "APROFUNDANDO",
        "SINTETIZANDO",
        "PRATICANDO",
        "EXERCITANDO",
        "RECAPITULANDO",
        "VIDEO"
    ]

    secao = None
    subsecao = None #preciso validar a lógica da subsecao com eles, eles fizeram os cursos em 2 etapas, secao e unidades
    unidade_atual = []
    unidades = []

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for para in doc.paragraphs:
        texto = para.text.strip()

        if texto.startswith("Capítulo"):
            if secao:
                if unidade_atual:
                    unidades.append({"unidade": unidade_atual})
                secao["unidades"] = unidades
                salvar_json_individual(secao, output_folder)

            secao = {
                "secao": texto,
                "subsecao": None,
                "unidades": []
            }
            unidades = []
            unidade_atual = []

        elif texto.startswith("subsecao:"):
            if secao:
                secao["subsecao"] = texto.split("subsecao:")[1].strip()

        elif any(texto.startswith(keyword) for keyword in UNIT_KEYWORDS):
            if unidade_atual:
                unidades.append({"unidade": unidade_atual})
                unidade_atual = []
            unidade_atual.append(texto)
        elif secao and unidade_atual:
            unidade_atual.append(texto)
    if secao:
        if unidade_atual:
            unidades.append({"unidade": unidade_atual})
        secao["unidades"] = unidades
        salvar_json_individual(secao, output_folder)


def salvar_json_individual(secao, output_folder):
    filename = f"{secao['secao'].replace(' ', '_').replace(':', '').replace('/', '_')}.json"
    filepath = os.path.join(output_folder, filename)
    with open(filepath, "w", encoding="utf-8") as json_file:
        json_file.write('[')
        json.dump(secao, json_file, indent=4, ensure_ascii=False)
        json_file.write(']')
    # print(f"Arquivo JSON salvo: {filepath}")


#=========================rota de upload do docx================================

@app.route('/upload-docx', methods=['POST'])
def upload_docx():
    file = request.files.get('docx_file')  # coloquei um id html teste para o docx file
    if not file:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    
    pasta_docx = os.path.abspath("oficial_pasta_envio")
    pasta_jsons = os.path.abspath("jsons")
    
    limpar_pastas(pasta_docx, pasta_jsons)
    
    docx_path = os.path.join(pasta_docx, file.filename)
    try:
        file.save(docx_path)
        processar_documento(docx_path, pasta_jsons) 
        return jsonify({
            "message": "Arquivo processado com sucesso",
            "output_folder_jsons": pasta_jsons,
            "uploaded_docx_folder": pasta_docx
        }), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao processar o documento: {str(e)}"}), 500


#==========================FIM DA GERAÇÃO DOS JSONS=========================================

#==============================rota do envio pdf============================================

@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    file = request.files.get('pdf_file') # aqui é o id referente ao pdf
    if not file:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    pasta_pdf = os.path.abspath("oficial_pasta_envio")
    
    if os.path.exists(pasta_pdf):
        for file_name in os.listdir(pasta_pdf):
            if file_name.endswith('.pdf'):
                file_path = os.path.join(pasta_pdf, file_name)
                try:
                    os.unlink(file_path)
                except Exception as e:
                    return jsonify({"error": f"Erro ao limpar arquivos antigos: {str(e)}"}), 500
    else:
        os.makedirs(pasta_pdf, exist_ok=True) 
    
    pdf_path = os.path.join(pasta_pdf, file.filename)
    
    try:
        file.save(pdf_path) 
        return jsonify({
            "message": "Arquivo processado com sucesso",
            "uploaded_pdf_folder": pasta_pdf
        }), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao processar o documento: {str(e)}"}), 500


#========================rota de upload da imagem==================================
@app.route('/upload-images', methods=['POST'])
def upload_images():
    file = request.files.get('png_file')
    if not file:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    pasta_images = os.path.abspath("oficial_pasta_envio")
    if os.path.exists(pasta_images):
        for file_name in os.listdir(pasta_images):
            if file_name.endswith('.png'):
                file_path = os.path.join(pasta_images, file_name)
                try:
                    os.unlink(file_path) 
                except Exception as e:
                    return jsonify({"error": f"Erro ao limpar arquivos antigos: {str(e)}"}), 500
    else:
        os.makedirs(pasta_images, exist_ok=True)

    image_path = os.path.join(pasta_images, file.filename)
    
    try:
        file.save(image_path) 
        return jsonify({
            "message": "Imagem processada com sucesso",
            "uploaded_image_folder": pasta_images
        }), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao processar a imagem: {str(e)}"}), 500


#====================funcao de criação da pasta assets, imagino que as imagens vão vir aqui, por enquanto está vazia=============================
def create_assets(base_path):
    assets_path = os.path.join(base_path, 'assets')

    os.makedirs(assets_path, exist_ok=True)

    assets_file_path = os.path.join(assets_path, 'assets.xml')
    with open(assets_file_path, 'w', encoding='utf-8') as f:
        f.write('<assets/>')

    # print("Pasta 'assets' criada com o arquivo 'assets.xml'.")



#======================criação da pasta policies, até onde entedi dela, aqui podemos manipular e criar as abas  do menu que ficam visiveis=========
#é possivel setar todos os dados da informacao do curso por aqui, incluindo inicip, exames, creio que há muito mais funcionalidades que automatizem de tudo no curso
#aqui parece ser um buraco de conhecimento que futuramente pode ser mais explorado
def create_policy_structure(base_path,nome_curso_input):
    policies_path = os.path.join(base_path, 'policies', '2025_T4')
    os.makedirs(policies_path, exist_ok=True)

    static_course_path = os.path.join(base_path, 'static')

    if os.path.exists(static_course_path):
        for file_name in os.listdir(static_course_path):
            file_path = os.path.join(static_course_path, file_name)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path) 
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

    os.makedirs(static_course_path, exist_ok=True)

    source_path = os.path.join('oficial_pasta_envio')
    if os.path.exists(source_path):
        for file_name in os.listdir(source_path):
            if file_name.endswith('.pdf') or file_name.endswith('.png'):
                src_file = os.path.join(source_path, file_name)
                dest_file = os.path.join(static_course_path, file_name)
                shutil.copy(src_file, dest_file)
    else:
        print(f"Diretório de origem não encontrado.")

    pdf_found = False
    png_found = False

    for file_name in os.listdir(static_course_path):
        if file_name.endswith('.pdf'):
            pdf_livro_off = file_name
            print(f"Este é o nome do livro OFF: {pdf_livro_off}")
            pdf_found = True
        elif file_name.endswith('.png'):
            png_image = file_name
            print(f"Este é o nome da imagem OFF: {png_image}")
            png_found = True

    if not pdf_found:
        print("Nenhum PDF foi encontrado na pasta static.")
    if not png_found:
        print("Nenhuma imagem png foi encontrada na pasta static.")
        

    policy_data = {
     "course/2025_T4": {
        "cert_html_view_enabled": True,
        "course_image": png_image,
        "discussion_topics": {
            "Geral": {
                "id": "course"
            }
        },
        "discussions_settings": {
            "enable_graded_units": False,
            "enable_in_context": True,
            "provider_type": "openedx",
            "unit_level_visibility": True
        },
        "display_name": nome_curso_input,
        "enable_timed_exams": True,
        "minimum_grade_credit": 0.8,
        "language": "pt",
        "pdf_textbooks": [
            {
                "chapters": [
                    {
                        "title": "Capitulo1",
                        "url": f"/static/{pdf_livro_off}"
                    }
                ],
                "id": "3PDF_TEXTO_LIVRO",
                "tab_title": "livro do estudante OFF"
            }
        ],
        "start": "2025-01-01T00:00:00Z",
        "tabs": [
            {
                "course_staff_only": False,
                "name": "Course",
                "type": "courseware"
            },
            {
                "course_staff_only": False,
                "name": "Progress",
                "type": "progress"
            },
            {
                "course_staff_only": False,
                "name": "Dates",
                "type": "dates"
            },
            {
                "course_staff_only": False,
                "name": "Discussion",
                "type": "discussion"
            },
            {
                "course_staff_only": False,
                "name": "Wiki",
                "type": "wiki"
            },
            {
                "course_staff_only": False,
                "name": "Textbooks",
                "type": "textbooks"
            },
            {
            "course_staff_only": False,
            "name": "Textbooks",
            "type": "pdf_textbooks"
            }
        ]        
    }
}

    policy_file_path = os.path.join(policies_path, 'policy.json')

    with open(policy_file_path, 'w', encoding='utf-8') as f:
        json.dump(policy_data, f, indent=4)

    # print(f"Arquivo 'policy.json' criado em 'policies/2025_T4'.")


#====================ainda preciso entender melhor todos os atributos desse arquivo, porem ao que indica sao os pesos e valores das atividades====================
def create_grading_policy(base_path):
    policies_path = os.path.join(base_path, 'policies', '2025_T4')

    os.makedirs(policies_path, exist_ok=True)

    grading_policy = {
        "GRADER": [
            {
                "drop_count": 2,
                "min_count": 12,
                "short_label": "HW",
                "type": "Homework",
                "weight": 0.15
            },
            {
                "drop_count": 2,
                "min_count": 12,
                "type": "Lab",
                "weight": 0.15
            },
            {
                "drop_count": 0,
                "min_count": 1,
                "short_label": "Midterm",
                "type": "Midterm Exam",
                "weight": 0.3
            },
            {
                "drop_count": 0,
                "min_count": 1,
                "short_label": "Final",
                "type": "Final Exam",
                "weight": 0.4
            }
        ],
        "GRADE_CUTOFFS": {
            "Pass": 0.5
        }
    }

    grading_policy_file_path = os.path.join(policies_path, 'grading_policy.json')

    with open(grading_policy_file_path, 'w', encoding='utf-8') as f:
        json.dump(grading_policy, f, indent=4)

    # print(f"Arquivo 'grading_policy.json' criado em 'policies/2025_T4'.")


#============== pasta policies=====================================
def create_assets_json(base_path):

    policies_path = os.path.join(base_path, 'policies')

    os.makedirs(policies_path, exist_ok=True)

    assets_json_file_path = os.path.join(policies_path, 'assets.json')

    with open(assets_json_file_path, 'w', encoding='utf-8') as f:
        json.dump({}, f)

    # print(f"Arquivo 'assets.json' vazio criado em 'policies'.")


#====================arquivo course.xml principal para criação de curso===============
def create_course_xml(base_path):
    course_file_path = os.path.join(base_path, 'course.xml')

    course_content = '''<course url_name="2025_T4" org=".Edu" course="TU104"/>'''

    with open(course_file_path, 'w', encoding='utf-8') as f:
        f.write(course_content)

    # print(f"Arquivo 'course.xml' criado em '{base_path}'.")


#=================keywords para separar as unidades=====================================

ordem_unidades = [
    "CONTEXTUALIZANDO",
    "CONECTANDO",
    "APROFUNDANDO",
    "SINTETIZANDO",
    "PRATICANDO",
    "EXERCITANDO",
    "RECAPITULANDO",
    "VIDEO"
]

unidade_inicial_map = {
    "CONTEXTUALIZANDO": "01",  
    "CONECTANDO": "02",        
    "APROFUNDANDO": "03", 
    "SINTETIZANDO": "04",     
    "PRATICANDO": "05",        
    "EXERCITANDO": "06",       
    "RECAPITULANDO": "07",     
    "VIDEO": "08"  
}



#=======================função para gerar html para cada unidade===========================
def gerar_html_unidade(curso_nome_input, chapter_name, unidade_nome):
    chapter_name_NFKD = unicodedata.normalize('NFKD', chapter_name).encode('ASCII', 'ignore').decode('ASCII')
    html_content = f'<!DOCTYPE html>\n<html lang="en">\n<head>\n'
    html_content += '    <meta charset="UTF-8">\n'
    html_content += '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
    html_content += f'    <title></title>\n</head>\n<body>\n'
    html_content += f'    <h1></h1>\n'
    html_content += f'    <p><iframe width="100%" style="min-height: 600px !important;" src="https://lexlam.com.br/fileserver/{curso_nome_input}/{chapter_name_NFKD}/{unidade_nome.lower()}/index.html" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></p>\n'
    html_content += '</body>'
    return html_content


chapter_ids = []  


# Criar a estrutura do curso/ pasta drafts + pasta chapter + pasta sequential + pasta course
def create_course_structure(base_path, data, course_path, year,curso_nome_input, course_name):
    
    files = os.listdir(course_path)
    docx_file = None
    for file in files:
        if file.endswith('.docx'):
            docx_file = file
            break
    if docx_file:
        file_name_course = os.path.splitext(docx_file)[0]
        # print(f"docx extraido {file_name_course}")
    else:
        print("Nenhum docx foi encontrado")

    # ======================== pasta course =======================================
    course_path = os.path.join(base_path, 'course')
    os.makedirs(course_path, exist_ok=True)
    
    course_filename = f"{year}_{course_name}.xml"
    course_file_path = os.path.join(course_path, course_filename)
    
    chapter_id = str(uuid.uuid4()) 

    # print(f'Este é o id do capítulo: {chapter_id} do json {data}')
    chapter_ids.append(chapter_id)
    
    chapters_xml = ""
    for chapter_id in chapter_ids:
        chapters_xml += f'  <chapter url_name="{chapter_id}"/>\n'
        # print(chapters_xml)

    course_content = f'''<course>
{chapters_xml}  <wiki slug="{org}+{random_sigla}+{course_id_ano}"/>
</course>'''

    # print(f'Este é o conteúdo do curso:\n{course_content}')
    
    with open(course_file_path, 'w', encoding='utf-8') as f:
        f.write(course_content)
    
    # print(f"Arquivo '{course_filename}' criado em 'course'.")
    
    # ======================== pasta chapter ====================================
    chapters_path = os.path.join(base_path, 'chapter')
    os.makedirs(chapters_path, exist_ok=True)

    for secao in data:
        chapter_name = secao.get('secao', 'Capítulo Desconhecido')
        try:
            chapter_number = int(chapter_name.split(" ")[1]) 
        except (IndexError, ValueError):
            chapter_number = 0  

        unique_id = f"{chapter_number:02d}-{uuid.uuid4().hex}"
        unique_filename_chapter = f"{chapter_id}.xml"

        chapter_file_path = os.path.join(chapters_path, unique_filename_chapter)

        # print(f"Criando o capítulo '{chapter_name}' com ID '{unique_id}'")

        with open(chapter_file_path, 'w', encoding='utf-8') as f:
            f.write(f'<chapter display_name="{chapter_name}">\n')
            f.write(f'    <sequential url_name="{unique_id}"/>\n')
            f.write('</chapter>\n')

        # print(f"Arquivo '{unique_filename_chapter}' criado em 'chapter'.")

    # ======================== pasta drafts =======================================
    drafts_path = os.path.join(base_path, 'drafts')
    html_path = os.path.join(drafts_path, 'html')
    vertical_path = os.path.join(drafts_path, 'vertical')

    os.makedirs(html_path, exist_ok=True)
    os.makedirs(vertical_path, exist_ok=True)

    vertical_ids = []

    for secao_data in data:
        if 'unidades' in secao_data:
            unidades = secao_data['unidades']
            
            for unidade_data in unidades:
                unidade_nome = unidade_data["unidade"][0].split()[0]                
                
                if unidade_nome.upper().startswith("EXERCITANDO"):
                    print(f"Ignorar unidade exercitando - removida: {unidade_nome}")
                    continue

                prefixo_id = unidade_inicial_map.get(unidade_nome, str(uuid.uuid4()))
                vertical_id = f"{prefixo_id}-{str(uuid.uuid4())}"
                if vertical_id.startswith("07"):
                    print(f"\n\n\n ACHEIIIIIIIIIIIIIIII \n{vertical_id}\n\n")
                html_id = f"{prefixo_id}-{str(uuid.uuid4())}"
                vertical_ids.append(vertical_id)

                unidade_text_list = unidade_data.get('unidade', [])
                unidade_text = "\n".join(unidade_text_list)

                html_file_name = f"{html_id}.html"
                match = re.match(r'(\w+)\s+(\d+)', chapter_name)
                first_word = match.group(1)  
                number = match.group(2)    
                chapter_name_url = first_word + number
                html_content = gerar_html_unidade(curso_nome_input, chapter_name_url, unidade_nome)
                print(f'{course_name}\n{chapter_name_url}\n{unidade_nome}')

                html_file_path = os.path.join(html_path, html_file_name)
                with open(html_file_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)

                html_xml_file_name = f"{html_id}.xml"
                html_xml_content = f'''
    <html filename="{html_file_name}"/>
    '''
                html_xml_file_path = os.path.join(html_path, html_xml_file_name)
                with open(html_xml_file_path, 'w', encoding='utf-8') as f:
                    f.write(html_xml_content)

                vertical_file_name = f"{vertical_id}.xml"
                print(f"\n este é o capitulo {chapter_name}\n\n\n")
                vertical_content = f'''
    <vertical display_name="{unidade_nome}" parent_url="block-v1:FelipinhoTutoriais+TU01+2025_TU01+type@sequential+block@{unique_id}" index_in_children_list="0">
    <html url_name="{html_id}"/>
    </vertical>
    '''
                vertical_file_path = os.path.join(vertical_path, vertical_file_name)
                with open(vertical_file_path, 'w', encoding='utf-8') as f:
                    f.write(vertical_content)
        else:
            print("Campo 'unidades' não encontrado no JSON.")

    # ======================== criação de exercícios abertos/fechados =========================
    documento = data
    unidade_exercitando = None

    for secao in documento:
        for unidade in secao.get("unidades", []):
            if "EXERCITANDO" in unidade.get("unidade", []):
                unidade_exercitando = unidade
                break
        if unidade_exercitando:
            break

    if unidade_exercitando:
        problem_path = os.path.join(drafts_path, "problem")
        os.makedirs(problem_path, exist_ok=True)

        vertical_index = 1
        unidade_texto = unidade_exercitando["unidade"]

        idx = 0
        while idx < len(unidade_texto):
            linha = unidade_texto[idx]

            if linha.startswith("Questão"):
                numero_questao = linha.split(" ")[1]
                texto_questao = []
                alternativas = []
                gabarito = None
                idx += 1

                while idx < len(unidade_texto) and not unidade_texto[idx].startswith("Questão"):
                    linha_atual = unidade_texto[idx].strip()
                    if linha_atual.startswith("a)") or linha_atual.startswith("b)") or linha_atual.startswith("c)") or linha_atual.startswith("d)"):
                        alternativas.append(linha_atual)
                    elif linha_atual.startswith("Gabarito:"):
                        gabarito = linha_atual.split(":")[-1].strip()
                    else:
                        texto_questao.append(linha_atual)
                    idx += 1

                texto_questao = " ".join(filter(None, texto_questao))

                # Lógica para questão fechada
                if alternativas:
                    xml_conteudo = f"""<problem display_name="Vamos exercitar" markdown="{texto_questao}">
        <multiplechoiceresponse>
            <p>Questão {numero_questao}</p>
            <label>{texto_questao}</label>
            <description></description>
            <choicegroup>
    """
                    for alternativa in alternativas:
                        letra_alternativa = alternativa.split(")")[0]
                        correct = "true" if letra_alternativa == gabarito else "false"
                        xml_conteudo += f'            <choice correct="{correct}">{alternativa}</choice>\n'
                    xml_conteudo += """        </choicegroup>
        </multiplechoiceresponse>
    </problem>"""
                else:
                    # Lógica para questão aberta
                    xml_conteudo = f"""<problem display_name="Vamos exercitar" markdown="texto_exercicio">
        <stringresponse answer="ola" type="ci">
            <p>{texto_questao}</p>
            <label>Insira sua resposta aqui</label>
            <description>resposta:</description>
            <additional_answer answer="Ola"/>
            <textline size="20"/>
        </stringresponse>
    </problem>"""

                xml_filename = f"{uuid.uuid4().hex}.xml"
                xml_id = xml_filename.removesuffix(".xml")
                xml_path = os.path.join(problem_path, xml_filename)

                with open(xml_path, 'w', encoding='utf-8') as xml_file:
                    xml_file.write(xml_conteudo)

                vertical_conteudo = f"""<vertical display_name="EXERCITANDO" parent_url="block-v1:edX+DemoX+Demo_Course+type@sequential+block@{unique_id}" index_in_children_list="{idx}">
        <problem url_name="{xml_id}"/>
    </vertical>"""

                vertical_xml_filename = f"06-{uuid.uuid4()}.xml"
                vertical_ids.append(vertical_xml_filename.removesuffix(".xml"))
                vertical_xml_path = os.path.join(vertical_path, vertical_xml_filename)

                with open(vertical_xml_path, 'w', encoding='utf-8') as vertical_xml_file:
                    vertical_xml_file.write(vertical_conteudo)

                vertical_index += 1
            else:
                idx += 1

    # ======================== pasta sequencial =======================================
    def get_display_name(unique_id):
        for name, prefix in unidade_inicial_map.items():
            if unique_id.startswith(prefix):
                return name

    sequential_path = os.path.join(base_path, 'sequential')
    os.makedirs(sequential_path, exist_ok=True)
    unique_filename = unique_id + ".xml"

    sequential_file_path = os.path.join(sequential_path, unique_filename)
    sequential_content = f'''<sequential display_name="Subseção 1">\n'''
    vertical_ids.sort()

    for vertical_id in vertical_ids:
        print(vertical_id)
        display_name = get_display_name(vertical_id)
        sequential_content += f'  <vertical url_name="{vertical_id}" display_name="{display_name}"/>\n'

    sequential_content += '</sequential>'

    with open(sequential_file_path, 'w', encoding='utf-8') as f:
        f.write(sequential_content)



#=================funcao de compressão de pastas para tar.gz==================
def compress_course_folder(base_path):
    try:
        tar_file_path = f"{base_path}.tar.gz"
        with tarfile.open(tar_file_path, "w:gz") as tar:
            tar.add(base_path, arcname=os.path.basename(base_path))
        print(f"A pasta '{base_path}' foi compactada como '{tar_file_path}'.")
        if not os.path.exists(tar_file_path):
            print(f"Erro: Arquivo compactado {tar_file_path} não foi criado.")
    except Exception as e:
        print(f"Erro ao compactar a pasta: {str(e)}")



#============geração de sigla identificadora de curso===================
def generate_random_sigla(length=5):
    return ''.join(random.choices(string.ascii_uppercase, k=length))


gerador_random_sigla = generate_random_sigla()  
current_year = datetime.now().year 
org = "IPGC"  
random_sigla = generate_random_sigla(5)
course_id = org +"+"+ random_sigla +"+"+ str(current_year) + "_" + random_sigla
course_id_ano = str(current_year) + "_" + random_sigla
# print(course_id) 

#=================nome do curso=======================
directory = 'oficial_pasta_envio'
for file in os.listdir(directory):
        if file.endswith(".docx"):
            nome_curso = file.split('_')[0]
            docx_path = os.path.join(directory,file)
output_folder = "jsons"
print(f"\n\n\n {nome_curso} \n\n\n")

#==================criaçao de curso via api===========================
def create_course_api(nome_curso, current_year, org, random_sigla):
    payload = {
    "title": f"{nome_curso}",
    "org": org,
    "number": random_sigla,
    "run": f"{current_year}_{random_sigla}",
    "schedule": {  
        "start": "2025-01-01T00:00:00Z",
        "end": "2025-12-31T23:59:59Z",
        "enrollment_start": "2024-12-01T00:00:00Z",
        "enrollment_end": "2025-01-31T23:59:59Z"
    }  
}

    headers = {
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url=f"{API_URL}/courses/create", headers=headers, json=payload)
        print(f"Payload enviado para criação de curso: {json.dumps(payload, indent=4)}")
        print(f"Response status code: {response.status_code}")
        print(f"Response text: {response.text}")
        if response.status_code == 200:
            print("Curso criado com sucesso!")
        else:
            print(f"Erro ao criar o curso: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Erro ao tentar criar o curso via API: {str(e)}")

#=======================importação de curso via api======================
def import_course_api(course_id):
    url = f"{API_URL}/courses/import"
    file_path = "./course/.tar.gz"

    if not os.path.exists(file_path):
        print(f"Arquivo {file_path} não encontrado. Verifique a compressão da pasta do curso.")
        return

    try:
        data = {"courseId": f"course-v1:{course_id}"}
        with open(file_path, "rb") as file:
            files = {"file": file}
            response = requests.post(url, data=data, files=files)
            print(f"Payload enviado para importação: {data}")
            print(f"Response status code: {response.status_code}")
            print(f"Response text: {response.text}")
            if response.status_code == 200:
                print("Curso importado com sucesso!")
            else:
                print(f"Erro ao importar curso: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Erro ao tentar importar o curso via API: {str(e)}")


#===================chamando as funcoes principais================
#==================rota de confirmar envio onde processa e sobe o curso==================
def restart_program():
    """Função para reiniciar o programa."""
    python = sys.executable
    os.execl(python, python, *sys.argv)

@app.route('/processar-cursos', methods=['POST'])
def processar_cursos():
    data = request.get_json() 
    course_name_input = data.get('name')
    print(course_name_input) 
    if not course_name_input:
        return jsonify({"error": "Nome do curso não fornecido"}), 400

    json_folder = 'jsons/'
    output_folder = 'course/' 
    shutil.rmtree(output_folder) 
    print(f"Removendo pasta existente: {output_folder}")
    os.makedirs(output_folder, exist_ok=True) 
    print(f"Pasta recriada: {output_folder}")

    if not os.path.exists(json_folder):
        return jsonify({"error": "A pasta jsons não foi encontrada"}), 400

    file_names = sorted(os.listdir(json_folder))
    if not file_names:
        return jsonify({"error": "Não há arquivos JSON na pasta jsons"}), 400

    for file_name in file_names:
        file_path = os.path.join(json_folder, file_name)
        with open(file_path, 'r', encoding='utf-8') as arq:
            data = json.load(arq)
            # print(data)
            course_path = os.path.join('oficial_pasta_envio')
            output_folder = os.path.join('course/')
            os.makedirs(output_folder, exist_ok=True)
            create_assets(output_folder)
            create_policy_structure(output_folder, course_name_input)
            create_grading_policy(output_folder)
            create_assets_json(output_folder)
            create_course_xml(output_folder)
            create_course_structure(output_folder,data,course_path, current_year,course_name_input, course_name="T4")
            compress_course_folder(output_folder)
    
    
    create_course_api(nome_curso, current_year, org, random_sigla)
    print("\nCURSO CRIADO\n")
    import_course_api(course_id) 
    print("\nCURSO IMPORTADO\n")
    print(f"nome do curso importado: {course_name_input}")
    
    chapter_ids.clear()

    # Não chama os._exit(0), permitindo que o servidor continue rodando
    return jsonify({"message": "Cursos processados e importados com sucesso"}), 200

if __name__ == "__main__":
    while True:
        try:
            app.run(debug=True, use_reloader=False)
        except Exception as e:
            print(f"Erro no servidor: {e}. Reiniciando...")
            time.sleep(5)  # Aguarda 5 segundos antes de reiniciar
