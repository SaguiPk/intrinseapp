from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.properties import ObjectProperty
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivymd.uix.button import MDButton, MDButtonText
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.dropdown import DropDown


class HomePage(Screen):
    pass

class Psicos(Screen):
    pass

class NomeCliente(Screen):
    pass

class EnvioMsg(Screen):
    pass


class HorariosTabela(ScrollView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, None)
        self.size = (800, 600)
        self.hora_select = None

        # Cria o GridLayout para os botões
        self.grid = GridLayout(cols=7, size_hint_y=None, spacing=10, padding=50)
        self.grid.bind(minimum_height=self.grid.setter('height'))

        # Gera os horários de meia em meia hora
        for hour in range(7, 21):  # De 7:00 até 21:30
            for minute in [30, 0] if hour == 7 else [0, 30]:
                if hour == 20 and minute == 30:
                    break
                time_label = f"{hour}:{minute:02d}"
                #btn = Button(text=time_label, size_hint_y=None, height=50)
                btn = MDButton(MDButtonText(text=f'{time_label}', bold=True, pos_hint={'center_x':.5, 'center_y': .5}, theme_font_size="Custom", font_size='25', theme_text_color="Custom", text_color=(130/255, 20/255, 235/255, 1), theme_font_name='Custom', font_name='Gotham-Rounded-Medium'), style="elevated", theme_bg_color="Custom", md_bg_color='white', radius=[11,], theme_width="Custom", height="55dp", width='40dp')
                btn.id = time_label
                btn.bind(on_press=lambda x: self.on_time_selected(x))
                self.grid.add_widget(btn)

        self.add_widget(self.grid)

    def reset_buttons(self):
        """Reset all buttons to their default state."""
        for button in self.grid.children:
            button.md_bg_color = 'white'  # Reset to default color
        self.hora_select = None  # Clear the selected time

    def on_time_selected(self, but):
        if self.hora_select == None:
            print(but.md_bg_color)
            if but.md_bg_color == [1.0, 1.0, 1.0, 1.0]:
                print("white")
                but.md_bg_color = [0.0, 0.8, 0.0, 1.0]
                self.hora_select = str(but.id)

        else:
            if but.md_bg_color == [1.0, 1.0, 1.0, 1.0]:
                self.reset_buttons()
                but.md_bg_color = [0.0, 0.8, 0.0, 1.0]
                self.hora_select = str(but.id)
            else:
                self.reset_buttons()

        print('horario selecionado:', self.hora_select)

            # if but.md_bg_color == [0.0, 0.8, 0.0, 1.0]:
        #     but.md_bg_color = 'white'
        #     self.hora_select = None
        # else:
        #     but.md_bg_color = [0.0, 0.8, 0.0, 1.0]  # Verde
        #     self.hora_select = str(but.id)
