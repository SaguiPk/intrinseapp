from kivy.network.urlrequest import UrlRequest
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.uix.button import MDButton, MDButtonText
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivymd.uix.dialog import MDDialog,MDDialogHeadlineText,MDDialogSupportingText,MDDialogButtonContainer,MDDialogContentContainer
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.progressindicator import MDLinearProgressIndicator
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText
from kivymd.uix.list import MDListItem, MDListItemHeadlineText


import certifi
import io
from datetime import datetime, timedelta
import json
import os.path
import time
import pandas as pd
import telebot
from dotenv import load_dotenv

from telas import *
from google_sheets import Url_Sheets, formt_text


class MainApp(MDApp):
    def build(self):
        # VERIFICAR SE HÁ INTERNET --------------------------------------------
        self.psico = ''
        self.horario = ''
        self.agenda_psico = None
        self.arq_nomes = None
        self.ids_teles = None
        self.txt_input_nome = StringProperty('')
        self.txt_input_hora = StringProperty('')
        self.agora = datetime.now()

        self.sheets = Url_Sheets()
        self.update_nomes_psis()

        self.dic_dias = {0:'SEGUNDA-FEIRA', 1:'TERCA-FEIRA', 2:'QUARTA-FEIRA', 3:'QUINTA-FEIRA', 4:'SEXTA-FEIRA'}   #, 5:'SABADO', 6:'DOMINGO'}
        self.dic_meses = {1:'janeiro', 2:'fevereiro', 3:'março', 4:'abril', 5:'maio', 6:'junho', 7:'julho', 8:'agosto', 9:'setembro', 10:'outubro', 11:'novembro', 12:'dezembro'}
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        load_dotenv(dotenv_path=env_path)
        print('token teleg'os.getenv('TOKEN_TELEG'))
        print('token teleg'os.getenv('URL_PLANILHA'))
        print('token teleg'os.getenv('COD_PLAN_KEY'))
        return Builder.load_file('main.kv')

    def check_internet(self, time=0):
        if not self.sheets.verif_conect():
            home = self.root.ids['homepage']
            texto = home.ids['id_conexao']
            texto.color = (1, 0, 0, 1)
            texto.text = 'Sem conexão'

            home = self.root.ids['homepage']
            home.ids['id_but_home'].disabled = True
            home.ids['id_enviar'].disabled = True
            self.casa()
            return False
        else:
            home = self.root.ids['homepage']
            texto = home.ids['id_conexao']
            texto.color = (0, 1, 0, 1)
            texto.text = 'Conectado'

            home = self.root.ids['homepage']
            home.ids['id_but_home'].disabled = False
            home.ids['id_enviar'].disabled = False
            return True

    def update_nomes_psis(self):
        nomes_file = 'jsons/nomes_psicos.json'
        ids_file = 'jsons/ids_teleg.json'
        tempo_val = 46800  # 13 horas em segundos

        def ler_json(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        def salvar_json(file_path, data):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

        def sem_net():
            #print('sem internet')
            home = self.root.ids['homepage']
            texto = home.ids['id_conexao']
            texto.color = (1, 0, 0, 1)
            texto.text = 'Sem conexão'
            home.ids['id_but_home'].disabled = True
            home.ids['id_enviar'].disabled = True
            self.casa()

        def fetch_and_update():
            #print('requisição necessária')
            nomes_ids = self.sheets.nomes_ids()
            if not nomes_ids[0]:
                sem_net()
                return False
            #print('com net, distribuir os valores')
            salvar_json(nomes_file, nomes_ids[0])
            salvar_json(ids_file, nomes_ids[1])
            self.arq_nomes = list(nomes_ids[0].keys())
            self.ids_teles = nomes_ids[1]
            return True

        # Verifica se os arquivos existem
        if os.path.exists(nomes_file):
            #print('arquivos existem')
            # Verifica se o arquivo está fora da validade
            if time.time() - os.path.getmtime(nomes_file) > tempo_val:
                #print('arquivos velhos, requeri-los')
                fetch_and_update()
            else:
                #print('arq dentro da validade')
                self.arq_nomes = list(ler_json(nomes_file).keys())
                self.ids_teles = ler_json(ids_file)
        else:
            #print('arquivos não existem')
            fetch_and_update()

    def atualizar_hora(self, dt):
        #locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
        self.agora = datetime.now()
        self.hora_formatada = self.agora.strftime("%H:%M")
        self.label_hr.text = self.hora_formatada


    def on_start(self):
    # RELOGIO E DATA ---------------------------------------------------------------------

        label_dia = self.root.ids['homepage']
        label_dia = label_dia.ids['id_dia']
        if self.agora.weekday() >= 5:  # Se for sábado ou domingo
            label_dia.text = f'final de semana {self.agora.day} de {self.dic_meses[self.agora.month]} de {self.agora.year}' #dia4
        else:
            label_dia.text = f'{self.dic_dias[self.agora.weekday()].lower()}, {self.agora.day} de {self.dic_meses[self.agora.month]} de {self.agora.year}'  # dia4

        self.label_hr = self.root.ids['homepage']
        self.label_hr = self.label_hr.ids['id_horario']

        Clock.schedule_interval(self.atualizar_hora, 1)

    # FAZ A CONEXAO COM A PLANILHA --------------------------------------------------------
        self.psico_select = {}
        conexao = self.sheets.conexao

        if conexao:
            home = self.root.ids['homepage']
            texto = home.ids['id_conexao']
            texto.color = (0,1,0,1)
            texto.text = 'Conectado'
            home = self.root.ids['homepage']
            home.ids['id_but_home'].disabled = False
            home.ids['id_enviar'].disabled = False

        else:
            home = self.root.ids['homepage']
            texto = home.ids['id_conexao']
            texto.color = (1,0,0,1)
            texto.text = 'Sem conexão'
            home = self.root.ids['homepage']
            home.ids['id_but_home'].disabled = True
            home.ids['id_enviar'].disabled = True

        def selecionar(but):
            ps = self.root.ids['psicos']
            ps.ids['id_progresso'].active = True
            ps.ids['id_layout_progresso'].opacity = 1
            self.psico = but.id

            nome_cliente = self.root.ids['nomecliente']
            msg_erro = nome_cliente.ids['msg_erro']
            msg_erro.text = 'DIGITE SEU [b]NOME[/b] E [b]HORÁRIO[/b]'

            pasta = f'agendas/agenda_{self.psico}.csv'
            tempo_val = 3600  # 1 hora em segundos

            def sem_net():
                #print('sem internet')
                home = self.root.ids['homepage']
                ps = self.root.ids['psicos']
                texto = home.ids['id_conexao']
                texto.color = (1, 0, 0, 1)
                texto.text = 'Sem conexão'
                ps.ids['id_progresso'].active = False
                ps.ids['id_layout_progresso'].opacity = 0
                home.ids['id_but_home'].disabled = True
                home.ids['id_enviar'].disabled = True
                self.casa()

            def requerir_plan(id_psico, sucesso_callback=None):
                #print('buscando planilha')
                url = os.getenv('URL_PLANILHA')  # URL da planilha
                url = f'{url}export?gid={str(id_psico)}&range=A:F&format=csv'

                def sucesso(req, result):
                    if not result:
                        sem_net()
                        #print("Nenhum dado recebido!")
                    else:
                        if isinstance(result, bytes):
                            result_str = result.decode('utf-8')
                        else:
                            result_str = result

                        df = pd.read_csv(io.StringIO(result_str), header=None)
                        # Define cabeçalho de forma dinâmica
                        header_row = 1 if df.iloc[0].isnull().all() else 0
                        df.columns = df.iloc[header_row]
                        df = df[header_row + 1:].reset_index(drop=True)

                        df.columns = [col if i != 2 else 'TERCA-FEIRA' for i, col in enumerate(df.columns)]

                        df.fillna(value=pd.NA, inplace=True)
                        self.agenda_psico = df
                        df.to_csv(pasta, sep=';', decimal=',', index=False, header=True, encoding='utf-8')
                        #print(self.agenda_psico)
                        if sucesso_callback:
                            sucesso_callback(df)


                def redirect(request, result):
                    redirect_url = request.resp_headers.get('Location')
                    # Tenta seguir o redirecionamento manualmente
                    if redirect_url:
                        #print("Seguindo redirecionamento manualmente...")
                        UrlRequest(url=redirect_url, on_success=sucesso, on_failure=on_failure, timeout=10, ca_file=certifi.where(), on_error=on_erro, method='GET')
                    else:
                        #print('redirecionametno não encontrado')
                        sem_net()

                def on_failure(request, result):
                    #print(f"Falha na requisição: {result[:200]}")
                    sem_net()

                def on_erro(req, result):
                    #print(f'sem internet: {result}')
                    sem_net()

                UrlRequest(url=url, on_success=sucesso, timeout=10, ca_file=certifi.where(), on_redirect=redirect, on_failure=on_failure, on_error=on_erro, method='GET')


            def on_sucess(df):
                ps.ids['id_layout_progresso'].opacity = 0
                ps.ids['id_progresso'].active = False
                gerenciador_tela = self.root.ids['screen_manager']
                gerenciador_tela.current = 'nomecliente'


            # Verifica se o arquivo existe e sua validade
            if os.path.exists(pasta):
                if time.time() - os.path.getmtime(pasta) > tempo_val:
                    print('arquivo antigo, atualizando')
                    os.remove(pasta)
                    with open('jsons/nomes_psicos.json', 'r', encoding='utf-8') as f:
                        id_psico = json.load(f)[self.psico]
                    requerir_plan(int(id_psico), on_sucess)

                else:
                    print('arquivo válido')
                    self.agenda_psico = pd.read_csv(pasta, sep=';')
                    on_sucess(df=None)
            else:
                print('arquivo não existe')
                with open('jsons/nomes_psicos.json', 'r', encoding='utf-8') as f:
                    id_psico = json.load(f)[self.psico]
                requerir_plan(int(id_psico), on_sucess)

            print(self.agenda_psico)


    # CRIA OS BOTÕES COM OS NOMES DOS PACIENTES ---------------------------------------
        if conexao:
            for psico in self.arq_nomes:
                but = MDButton(MDButtonText(text=f'{psico}', bold=True, pos_hint={'center_x':.5, 'center_y': .5}, theme_font_size="Custom", font_size='30', theme_text_color="Custom", text_color=(130/255, 20/255, 235/255, 1), theme_font_name='Custom', font_name='Gotham-Rounded-Medium'), style="elevated", theme_bg_color="Custom", md_bg_color='white', radius=[11,], theme_width="Custom", height="70dp", size_hint_x= 0.5)
                but.id = f'{psico}'
                page_psicos =self.root.ids['psicos']
                page_psicos.ids['main_scroll'].add_widget(but)
                but.bind(on_press=lambda x: selecionar(x))
                self.psico_select[but] = psico
        else:
            home = self.root.ids['homepage']
            home.ids['id_but_home'].disabled = True

    def mudar_tela(self, id_tela):
        tela_psicos = self.root.ids['psicos']
        gerenciador_tela = self.root.ids['screen_manager']
        gerenciador_tela.current = id_tela

    def voltar(self, time=0):
        if self.root.ids['screen_manager'].current == 'enviomsg':
            gerenciador_tela = self.root.ids['screen_manager']
            nome_cliente = self.root.ids['nomecliente']
            input = nome_cliente.ids['id_input']
            input_hora = nome_cliente.ids['id_input_hora']
            envio_msg = self.root.ids['enviomsg']
            texto_msg = envio_msg.ids['id_msg']
            nome_cliente = self.root.ids['nomecliente']
            msg_erro = nome_cliente.ids['msg_erro']
            msg_erro.text = ' '
            texto_msg.text = ''
            input.text = ''
            input_hora.text = ''
            gerenciador_tela.current = 'homepage'
            hr_tabela = nome_cliente.ids['id_input_hora']
            hr_tabela.reset_buttons()

    def casa(self, time=0):
        gerenciador_tela = self.root.ids['screen_manager']
        nome_cliente = self.root.ids['nomecliente']
        input = nome_cliente.ids['id_input']
        input_hora = nome_cliente.ids['id_input_hora']
        envio_msg = self.root.ids['enviomsg']
        texto_msg = envio_msg.ids['id_msg']
        nome_cliente = self.root.ids['nomecliente']
        msg_erro = nome_cliente.ids['msg_erro']
        msg_erro.text = 'DIGITE SEU [b]NOME[/b] E [b]HORÁRIO[/b]'
        texto_msg.text = ''
        input.text = ''
        input_hora.text = ''
        self.txt_input_nome = None
        self.txt_input_hora = None
        self.psico = None
        gerenciador_tela.current = 'homepage'
        hr_tabela = nome_cliente.ids['id_input_hora']
        hr_tabela.reset_buttons()

    def verificador(self, nome_paciente, horario_paciente):

        self.txt_input_nome = nome_paciente.text
        self.txt_input_hora = horario_paciente.hora_select
        print(self.txt_input_hora)
        print(self.txt_input_nome)
        print(self.txt_input_nome, type(self.txt_input_hora))

        n = ''

        def dia_hoje():
            dia_hoje = self.agora.weekday()  # f'{self.agora.strftime("%A")}'
            if dia_hoje >= 5:
                return 'final de semana'
            else:
                dia_hoje = self.dic_dias[dia_hoje]
                return dia_hoje
        #if self.check_internet():

        # Verificar se é final de semana // OK - PARA TESTE //
        if self.agora.weekday() >= 5:
            nome_cliente = self.root.ids['nomecliente']
            msg_erro = nome_cliente.ids['msg_erro']
            msg_erro.text = 'FINAL DE SEMANA  ;) '
            msg_erro.color = (0, 1, 0, 1)
            Clock.schedule_once(callback=lambda dt: (setattr(msg_erro, 'text', 'DIGITE SEU [b]NOME[/b] E [b]HORÁRIO[/b]'),setattr(msg_erro, 'color', (1, 1, 1, 1))), timeout=5)
        # Hoje é DIA UTIL ------
        else:
            # Campos <nome_input> e <hora_input> PREENCHIDOS -----
            if self.txt_input_nome != '' and self.txt_input_hora != None and isinstance(self.txt_input_nome, str): # Verifica se os campos estão vazios, se não estiver vazio:
                print('campos preenchidos')
                tela_enviomsg = self.root.ids['enviomsg']
                id_msg = tela_enviomsg.ids['id_msg']
                id_msg.text = ''

                self.paciente = nome_paciente.text
                self.horario = horario_paciente.hora_select
                # -------------------------------------------------------------------
                # if ':' not in self.horario:
                #     self.horario = self.horario[:2] + ':' + self.horario[2:]
                #     if self.horario[0] == '0':
                #         self.horario = self.horario[1:]
                #agendas = pd.read_excel(r'HORÁRIOS.xlsx', sheet_name=None)

                # colunas = list(self.agenda_psico.keys())
                #lista_dias = ['SEGUNDA-FEIRA', 'TERCA-FEIRA', 'QUARTA-FEIRA', 'QUINTA-FEIRA', 'SEXTA-FEIRA'] #colunas[1:-4]  # 5 dias
                # -----------------------------------------------------------------------------------------------------------------------

                df_hrs = self.agenda_psico['HORA/DIA']  # HORARIOS_DF -----        das 7h30 até 21h -> 28 horarios(linhas)
                #dic_hors = dict(df_hrs)

                dic_hors = {valor: chave for chave, valor in df_hrs.items()}  # DICT = { valor<'8:00'> : chave<'SANDRA APARECIDA'> }

                #locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# -------------- FUNÇÕES AUXILIARES ----------------------------------------------------

                def calcular_diferenca_em_segundos(hora1, hora2, tempo):

                    segundos1 = hora1.hour * 3600 + hora1.minute * 60
                    segundos2 = hora2.hour * 3600 + hora2.minute * 60
                    diferenca_segundos = segundos2 - segundos1

                    delta = timedelta(seconds=abs(diferenca_segundos))
                    horas, resto = divmod(delta.seconds, 3600)
                    minutos, segundos = divmod(resto, 60)

                    resultado = []

                    if diferenca_segundos <= 0:
                        if diferenca_segundos <= tempo:
                            resultado.append('Sessão já encerrada.\nConsulte a recepção.')
                        else:
                            resultado.append('Aguarde, você já será chamada(o).')
                    else:
                        if horas != 0:
                            # print(f'Sua sessão começará daqui a {horas}hrs {minutos}min {segundos}seg')
                            resultado.append(f'Começará daqui a {horas}hrs {minutos}min.\n\nEntão, sente-se e relaxe :)\n\nA Psicóloga(o), já foi avisada')
                        else:  # h=0
                            if minutos != 0:
                                # print(f'Sua sessão começará daqui a {horas}hrs {minutos}min {segundos}seg')
                                resultado.append(f'Começará daqui a {minutos}min.\n\nEntão, sente-se e relaxe :)\n\nA Psicóloga(o), já foi avisada')
                            else:  # h=0
                                if segundos != 0:
                                    # print(f'Sua sessão começará daqui a {horas}hrs {minutos}min {segundos}seg')
                                    resultado.append(f'Começará daqui a {segundos}seg.\n\n')
                                else:
                                    pass
                    return resultado

                def controle_datas(psico, paciente, data_hoje, convenio:str):
                    arquivo_csv = f'controles/controle_{psico}.csv'
                    # verificar se já existe o arq csv do psico
                    nome_coluna = f'{paciente} {convenio}'
                    valor = data_hoje

                    if not os.path.exists(arquivo_csv):
                        #print('arquivo não existe')
                        # se não existir criar
                        df = pd.DataFrame(columns=[nome_coluna])
                        df.loc[len(df)] = [valor]
                        df.to_csv(arquivo_csv, sep=';', decimal=',', index=False, header=True, encoding='utf-8')
                        #print(df)
                        return
                    else:
                        #print('arquivo existe')
                        # se existir ler
                        df = pd.read_csv(arquivo_csv, sep=';', encoding='utf-8')

                        # veriricar se dentro do arquivo existe o paciente como uma coluna
                        if nome_coluna not in df.columns:
                            #print('coluna não existe')
                            # se não existir adicionar
                            df[nome_coluna] = pd.NA
                        #print(df)
                        #print('coluna existe')
                        #print(len(df[nome_coluna]))

                        for i, val in enumerate(df[nome_coluna]):
                            #print(i, type(val))
                            if pd.isna(val):
                                #print(i, val)
                                df.loc[i, nome_coluna] = valor
                                df.to_csv(arquivo_csv, sep=';', decimal=',', index=False, header=True, encoding='utf-8')
                                #print('arquivo salvo!')
                                #print(df)
                                return

                        df.loc[len(df[nome_coluna]), nome_coluna] = valor
                        df.to_csv(arquivo_csv, sep=';', decimal=',', index=False, header=True, encoding='utf-8')

                        #print(df)
                    #print('finalizar controle de datas')

                def controle_fluxo(data, horario, convenio):
                    arquivo_csv = f'controles/controle_fluxo.csv'
                    nome_coluna = f'{data}'
                    valor = f'Pac {convenio} {horario}'

                    if not os.path.exists(arquivo_csv):
                        #print('arquico fluxo não existe')
                        # se não existir criar
                        df = pd.DataFrame(columns=[nome_coluna])
                        df.loc[len(df)] = [valor]
                        df.to_csv(arquivo_csv, sep=';', decimal=',', index=False, header=True, encoding='utf-8')
                        return
                    else:
                        #print('arquivo fluxo existe')
                        df = pd.read_csv(arquivo_csv, sep=';', encoding='utf-8')
                        if nome_coluna not in df.columns:
                            #print('coluna não existe')
                            # se não existir adicionar
                            df[nome_coluna] = pd.NA

                        #print(df)
                        #print('coluna existe')
                        #print(len(df[nome_coluna]))

                        for i, val in enumerate(df[nome_coluna]):
                            #print(i, type(val))
                            if pd.isna(val):
                                #print(i, val)
                                df.loc[i, nome_coluna] = valor
                                df.to_csv(arquivo_csv, sep=';', decimal=',', index=False, header=True, encoding='utf-8')
                                #print('arquivo salvo!')
                                #print(df)
                                return

                        df.loc[len(df[nome_coluna]), nome_coluna] = valor
                        df.to_csv(arquivo_csv, sep=';', decimal=',', index=False, header=True, encoding='utf-8')

                        #print(df)
# ----------------- ------------------------- ---------------------- --------------------------

                # EXTRAIR O DIA DE HOJE ----------
                dia_semana_hoje = [dia_hoje().upper(), self.dic_dias[0]] # varl p/ controle de teste
                chave_dsh = dia_semana_hoje[0] # CHAVE_DSH:str = <'SEGUNDA-FEIRA'>
                encontrou = False # CHAVE DE CONTROLE DE VERIFICAÇÃO --------

                # INICIAR A BUSCA DO PACIENTE NA AGENDA DO PSICO --------------------------------------
                if encontrou is False: # --< 1ª BUSCA >--> horario do dia
                    # Procurar a pessoa no HORARIO do dia de <hoje>
                    dia_semana = self.agenda_psico[f'{chave_dsh}'] # extrai o data frame da agenda do dia de hoje
                    print('agenda do dia de hoje\n', dia_semana)

                    try:
                        nome = dia_semana.iloc[dic_hors[self.horario]] # EXTRAI O NOME_DF_BD NO HORARIO_DF_SELECT
                        n, c = formt_text(str(nome))#.title())  TRATAR O NOME_DF_BD

                     # Verificar se o <NOME_INPUT>  IN <NOME_DF_BD>
                        if self.paciente.upper() in n:
                            print(f'encontrou o nome no dia de hoje: {n} {dia_hoje()} e horario {self.horario}')
                            encontrou = True # --- // ENCONTROU // ---

                            horarios_str = self.horario # --- EXTRAIR O HORARIO_DF_BD                    #df_hrs.iloc[i]
                            # EXTRAIR  horario_dt ----------
                            horarios = datetime.strptime(horarios_str, "%H:%M") # HORA_INP_DT --------
                            str_hrs = horarios.strftime("%H:%M") # string da hora <'08:00'>

                            paciente_seguinte = dia_semana.iloc[dic_hors[self.horario] +1] # EXTRAIR NOME.SEG_DF ------               #pacientes_dia.iloc[i + 1]
                            nps,cps = formt_text(str(paciente_seguinte)) # TRATAR O NOME.SEG ----------                            .title())

                            try: # verificar se relação = pac.seg / pac.atual ----------------------

                                if n in nps: # pac.seg==pac.atual
                                    tempo_sessao = -3600  # 1 hora // paciente de 1h
                                else:
                                    tempo_sessao = -1800  # 30 minutos // paciente de 30min
                            except: # se for valor nulo -----------------------------------------
                                tempo_sessao = -1800  # 30 minutos // paciente de 30min

                            # CALCULAR A DIFERENCA <'HORA.new()'>/<'HORA_INP_DT'>/<'TEMPO_SESS'    ==    </ TEXTO DE RESPOSTA:id_msg />
                            resultado = calcular_diferenca_em_segundos(self.agora.time(), horarios, tempo_sessao)
                            #controle_datas(self.psico, n, self.agora.strftime("%d/%m/%Y"), c)
                            #controle_fluxo(self.agora.strftime('%d/%m/%Y'), self.agora.strftime('%H:%M'), c)

                            id_msg.text = (f'[size=70]Bem Vindo {n}[/size]\n\n'  # ENVIAR TEXTO_DE_RESPOSTA  ---------------------
                                           f'[size=60]Hoje {chave_dsh.lower()} sua sessão é as {str_hrs}[/size]\n'
                                           f'[size=50]{resultado[0]}[/size]\n')


                            try: # TRATAR O ENVIO DA MENSAGEM BOT TELEGRAM -------------------
                                token = os.getenv('TOKEN_TELEG')
                                bot = telebot.TeleBot(token=token)
                                bot.send_message(chat_id=self.ids_teles[self.psico], text=f'{n.upper()}')  # text=f'{nome_paciente.text.upper()}')
                                Clock.schedule_once(callback=self.voltar, timeout=10)

                            except Exception as e: # SE FALAHAR O ENVIO
                                print(e)
                                # se der erro verificar a internt
                                id_msg.text = (f'[size=70][color=ff0000]ERRO DE CONEXÃO[/color][/size]\n'
                                               f'[size=50]Consulte a recepção por gentileza ;)[/size]')

                                Clock.schedule_once(callback=self.check_internet, timeout=10)

                            # TROCAR PARA ULTIMA TELA ----------------------
                            gerenciador_tela = self.root.ids['screen_manager']
                            gerenciador_tela.current = 'enviomsg' # trocar tela ------
                            # limpar compos textos ---------
                            nome_paciente.text = ''
                            horario_paciente.hora_select = None
                            n = ''
                            self.psico = None # limpar var.psico.selec

                    # Se <nome_input> NOT IN <nome_horario>
                        else:
                            # Passar a verificação para o dia da semana
                            pass
                    except Exception as e:
                        print(e)
                        pass # Se der errado o processo


                # Se não encontrou no horario de hoje, Procurar em outros horarios
                    if encontrou is False: # --< 2ª BUSCA >--> outros horarios do dia
                        n = ''

                        print(f'Não encontrou {self.paciente} no horario selecioado {self.horario} no dia de hoje {chave_dsh}')
                        # Procurar nos horarios do dia -----<
                        for i, pessoa in enumerate(self.agenda_psico[f'{chave_dsh}'].values):
                            if pessoa is pd.NA or pd.isna(pessoa) or pessoa == '' or pessoa is None:
                                continue

                            n, c = formt_text(str(pessoa))
                            print(self.paciente.upper(), n[:len(self.paciente) + 1])

                            if self.paciente.upper() in n[:len(self.paciente) + 1]:
                                horario_pessoa = df_hrs.iloc[i]
                                print(f'Pessoa encontrada no dia {chave_dsh}: {n} {horario_pessoa}')
                                encontrou = True # // ENCONTROU // ---

                                id_msg.text = (
                                    f'[size=70]Bem Vindo {n}[/size]\n\n'  # ENVIAR TEXTO_DE_RESPOSTA  ---------------------
                                    f'[size=60]Hoje {chave_dsh.lower()}, sua horário esta as: {horario_pessoa}[/size]\n',
                                    f'[size=60]Seu Psico já foi avisado ! | O . < |[/size]')

                                try:  # TRATAR O ENVIO DA MENSAGEM BOT TELEGRAM -------------------
                                    token = os.getenv('TOKEN_TELEG')
                                    bot = telebot.TeleBot(token=token)
                                    bot.send_message(chat_id=self.ids_teles[self.psico], text=f'{n.upper()}')
                                    Clock.schedule_once(callback=self.voltar, timeout=10)
                                    break
                                except:
                                    pass


                        # Se não encontrou no dia de hoje, procurar em outros dias da semana
                        if encontrou is False: # -- < 3ª BUSCA > --> outros dias da semana
                            print(f'pessoa não encontrada no dia de hoje: {chave_dsh}')
                            for dia in self.dic_dias.values():
                                if self.agenda_psico[f'{dia}'].isnull().all() or dia == chave_dsh:
                                    continue

                                for i, pessoa in enumerate(self.agenda_psico[f'{dia}'].values):
                                    if pessoa is pd.NA or pd.isna(pessoa) or pessoa == '' or pessoa is None:
                                        continue
                                    print(pessoa)
                                    n, c = formt_text(str(pessoa))

                                    if pd.notna(pessoa) and self.paciente.upper() in n[:len(self.paciente)+1]:
                                        horario_pessoa = df_hrs.iloc[i]
                                        print(f'pessoa encontrada no dia {dia}: {n} {horario_pessoa}')
                                        encontrou = True # // ENCONTROU // ---
                                        break
                                        #controle_datas(self.psico, n, self.agora.strftime("%d/%m/%Y"), c)

                                        #controle_fluxo(self.agora.strftime('%d/%m/%Y'), self.agora.strftime('%H:%M'), c)
                                if encontrou is True:
                                    id_msg.text = (
                                        f'[size=70]Bem Vindo {n}[/size]\n\n'  # ENVIAR TEXTO_DE_RESPOSTA  ---------------------
                                        f'[size=60]Sua sessão está no dia: {dia}, no horário: {horario_pessoa}[/size]\n',
                                        f'[size=60]Seu Psico já foi avisado ! | O . < |[/size]')

                                    try:  # TRATAR O ENVIO DA MENSAGEM BOT TELEGRAM -------------------
                                        token = os.getenv('TOKEN_TELEG')
                                        bot = telebot.TeleBot(token=token)
                                        bot.send_message(chat_id=self.ids_teles[self.psico], text=f'{n.upper()}')
                                        Clock.schedule_once(callback=self.voltar, timeout=10)
                                    except:
                                        pass
                                    break

                        # Se encontrou em algum dia e horario
                        if encontrou is True:
                            gerenciador_tela = self.root.ids['screen_manager']
                            gerenciador_tela.current = 'enviomsg'
                            nome_paciente.text = ''
                            horario_paciente.hora_select = None
                            n = ''
                            self.psico = None



                # Se depois de tudo não encontrou na agenda
                    if encontrou is False:  # Se não encontrar em nenhum dia
                        # não mudar de tela, notificar na tela nomecliente
                        nome_cliente = self.root.ids['nomecliente']
                        msg_erro = nome_cliente.ids['msg_erro']
                        msg_erro.text = (f'          Paciente não encontrado!\nConsulte a recepção por gentileza ;)')
                        Clock.schedule_once(callback=lambda dt: (setattr(msg_erro, 'text', 'DIGITE SEU [b]NOME[/b] E [b]HORÁRIO[/b]'), setattr(msg_erro, 'color', (1, 1, 1, 1))), timeout=5)

                # Se a chave <encontro> não atualizada <bug>
                else:
                    pass
                    #print('encontrou = True else linha 561')

                # gerenciador_tela = self.root.ids['screen_manager']
                # gerenciador_tela.current = 'enviomsg'
                # nome_paciente.text = ''
                # horario_paciente.text = ''

            # Tratar a situação de campos vazios
            else:
                print('campos não preenchidos')
                # Se o campo <nome_input> vazio e <hora_input> preenxido
                if self.txt_input_nome == '' and self.txt_input_hora != None and isinstance(self.txt_input_nome, str):
                    nome_cliente = self.root.ids['nomecliente']
                    msg_erro = nome_cliente.ids['msg_erro']
                    msg_erro.text = 'CAMPO NOME VAZIO'
                    msg_erro.color = (1, 0, 0, 1)
                    Clock.schedule_once(callback=lambda dt: (setattr(msg_erro, 'text', 'DIGITE SEU [b]NOME[/b] E [b]HORÁRIO[/b]'), setattr(msg_erro, 'color', (1,1,1,1))), timeout=5)

                # Se campo <nome_input> preensido e <hora_input> vazio
                elif self.txt_input_nome != '' and self.txt_input_hora == None and isinstance(self.txt_input_nome, str):
                    nome_cliente = self.root.ids['nomecliente']
                    msg_erro = nome_cliente.ids['msg_erro']
                    msg_erro.text = 'CAMPO HORÁRIO VAZIO'
                    msg_erro.color = (1, 0, 0, 1)
                    Clock.schedule_once(callback=lambda dt: (setattr(msg_erro, 'text', 'DIGITE SEU [b]NOME[/b] E [b]HORÁRIO[/b]'), setattr(msg_erro, 'color', (1,1,1,1))), timeout=5)

                # Se o campos <nome_input> e <hora_input> vazios
                elif self.txt_input_nome == '' and self.txt_input_hora == None and isinstance(self.txt_input_nome, str):
                    nome_cliente = self.root.ids['nomecliente']
                    msg_erro = nome_cliente.ids['msg_erro']
                    msg_erro.text = 'CAMPOS NOME E HORÁRIO VAZIO'
                    msg_erro.color = (1, 0, 0, 1)
                    Clock.schedule_once(callback=lambda dt: (setattr(msg_erro, 'text', 'DIGITE SEU [b]NOME[/b] E [b]HORÁRIO[/b]'), setattr(msg_erro, 'color', (1,1,1,1))), timeout=5)

            n = ''

    # função listar os nomes dos arquivos na pasta
    def get_file_list(self, folder_path):
        try:
            files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
            return files

        except FileNotFoundError:
            return []


    def enviar_arquivos(self):
        self.senha = None  #self.dialog #ids['content_container']  .content_cls.children[-3] .ids.senha_input
        self.widget_txfd = None
        self.progresso_wid = None
        for widget in self.dialog.walk():
            #print(widget)
            if isinstance(widget, MDTextField) and widget.id == 'senha_input':
                self.senha = widget.text
                #print(self.senha)
                self.widget_txfd = widget
                continue
            elif isinstance(widget, MDLinearProgressIndicator) and widget.id == 'progresso':
                self.progresso_wid = widget
                break

        if self.senha == 'intrinse':  # Substitua pela senha correta
            #field = self.dialog.get_ids()
            self.widget_txfd.line_color_normal = "green"

            #self.processar_proxima_iteracao(0)  # Inicia o processamento
        else:
            #field = self.dialog.get_ids()
            self.widget_txfd.line_color_normal="red"


    def processar_proxima_iteracao(self, dt):
        if self.current_index < self.total_arquivos:
            try:
                i = self.current_index
                nome = self.arq_nomes[i]
                contagem = ((i + 1) / self.total_arquivos) * 100

                # Atualiza a barra de progresso
                #progresso = self.dialog.get_ids()['progresso']
                self.progresso_wid.value = contagem

                #self.bot.send_message(chat_id=self.ids_teles['GUILHERME'], text=f'contagem {nome}')
                if os.path.exists(f'controles/controle_{nome}.csv'):
                    try:
                        self.bot.send_document(chat_id=self.ids_teles[nome], document=open(f'controles/controle_{nome}.csv', 'rb'))
                        os.remove(f'controles/controle_{nome}.csv')
                    except:
                        self.dialog.dismiss()
                        home = self.root.ids['homepage']
                        texto = home.ids['id_conexao']
                        texto.color = (1, 0, 0, 1)
                        texto.text = 'Sem conexão'
                        home = self.root.ids['homepage']
                        home.ids['id_but_home'].disabled = True
                        home.ids['id_enviar'].disabled = True

                if os.path.exists(f'controles/controle_fluxo.csv'):
                    try:
                        self.bot.send_document(chat_id=self.ids_teles['GUILHERME'],document=open(f'controles/controle_fluxo.csv', 'rb'))
                        os.remove(f'controles/controle_fluxo.csv')
                    except:
                        self.dialog.dismiss()
                        home = self.root.ids['homepage']
                        texto = home.ids['id_conexao']
                        texto.color = (1, 0, 0, 1)
                        texto.text = 'Sem conexão'
                        home = self.root.ids['homepage']
                        home.ids['id_but_home'].disabled = True
                        home.ids['id_enviar'].disabled = True

                # Avança para o próximo
                self.current_index += 1
                Clock.schedule_once(self.processar_proxima_iteracao, 0)
            except Exception as e:
                #print(e)
                self.dialog.dismiss()
        else:
            self.dialog.dismiss()

    def atualizar(self):
        #print('atualizar')
        self.but = None
        for widget in self.dialog.walk():
            if isinstance(widget, MDButton) and widget.id == 'atualizar':
                #print('Aguarde...')
                widget.theme_line_color = 'Custom'
                widget.line_color = 'red'
                self.but = widget
        def inic_atual(time=0):
            lista_arquivos = None
            # pegar os arquivos do diretorio nomes_psicos.json, ids_teleg.json, acessar a pasta agendas e limpá-la, e depois reinstalar o que foi removido
            if os.path.exists('jsons/nomes_psicos.json'):
                os.remove('jsons/nomes_psicos.json')
            if os.path.exists('jsons/ids_teleg.json'):
                os.remove('jsons/ids_teleg.json')

            if os.path.exists('agendas'):
                lista_arquivos = os.listdir('agendas')
                for file in lista_arquivos:
                    file_path = os.path.join('agendas', file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)

            #print(lista_arquivos)
            self.update_nomes_psis()
            #print('atualização finalizada')
            self.but.line_color = 'green'

        Clock.schedule_once(inic_atual, 1)


    def enviar_controles(self):
        try:
            folder_path = "controles/"  # Replace with your actual folder path
            file_list = self.get_file_list(folder_path)
            num_files = len(file_list)

            self.dialog = None
            self.current_index = 0
            self.total_arquivos = len(self.arq_nomes)
            self.bot = telebot.TeleBot(token=f"{os.getenv('TOKEN_TELEG')}") 


            # self.dialog = MDDialog(MDDialogHeadlineText(text="Enviar Controle de Datas"),
            #                  MDDialogSupportingText(text="Deseja enviar os controles de datas para os psicólogos?"),
            #                  MDDialogContentContainer(
            #                      MDTextField(MDTextFieldHintText(text="Senha", text_color_normal="gray"),mode="outlined", id='senha_input', theme_line_color="Custom", line_color_normal="gray",line_color_focus="blue", size_hint_x=1, password=True, pos_hint={"center_x": .5, "center_y": .5}),
            #                      Widget(size_hint_y=None, height=20),
            #                      MDLinearProgressIndicator(id='progresso', value=0, indicator_color='blue'), orientation='vertical'),
            #                  MDDialogButtonContainer(
            #                      MDButton(MDButtonText(text="Cancelar"), style="text", on_release=lambda x: self.dialog.dismiss()),
            #                      MDButton(MDButtonText(text="Enviar"), style="text", on_release=lambda x: enviar_arquivos()),spacing="310dp"))

            if not self.dialog:
                content = MDDialogContentContainer(orientation='vertical')

                # Display the number of files
                content.add_widget(MDLabel(text=f"Total de arquivos: {num_files}", halign="center"))
                content.add_widget(Widget(size_hint_y=None, height=10))  # Add some spacing

                # Create a ScrollView for the list of files
                scroll_view = ScrollView(size_hint=(1, None), size=(30, 100))
                file_list_layout = BoxLayout(orientation='vertical', size_hint_y=None)
                file_list_layout.bind(minimum_height=file_list_layout.setter('height'))

                for file_name in file_list:
                    file_label = MDLabel(text=file_name, size_hint_y=None, height=30)
                    file_list_layout.add_widget(file_label)

                scroll_view.add_widget(file_list_layout)
                content.add_widget(scroll_view)

                content.add_widget(Widget(size_hint_y=None, height=20))

                # Add the password input and progress indicator back
                content.add_widget(
                    MDTextField(hint_text="Senha", mode="outlined", id='senha_input', theme_line_color="Custom",
                                line_color_normal="gray", line_color_focus="blue", size_hint_x=1, password=True,
                                pos_hint={"center_x": .5, "center_y": .5}))
                content.add_widget(Widget(size_hint_y=None, height=20))
                content.add_widget(MDLinearProgressIndicator(id='progresso', value=0, indicator_color='blue'))

                self.dialog = MDDialog(
                    MDDialogHeadlineText(text="Enviar Controle de Datas"),
                    MDDialogSupportingText(text="Deseja enviar os seguintes controles de datas para os psicólogos?"),
                    content,
                    MDDialogButtonContainer(
                        MDButton(MDButtonText(text="Cancelar"), style="text", on_release=lambda x: self.dialog.dismiss()),
                        MDButton(MDButtonText(text='Atualizar'), id='atualizar', style='text', on_release=lambda x: self.atualizar()),
                        MDButton(MDButtonText(text="Enviar",), style="text", on_release=lambda x: self.enviar_arquivos()),
                        spacing="100dp"
                    )
                )

            self.dialog.open()
        except Exception as e:
            #print(e)
            self.dialog.dismiss()

MainApp().run()
