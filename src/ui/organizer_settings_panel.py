from tkinter import ttk

class OrganizerSettingsPanel:
    def __init__(self, master):
        self.master = master
        self.create_widgets()

    def create_widgets(self):
        self.label = ttk.Label(self.master, text='Feature Extractor')
        self.label.pack()

        self.model_selection = ttk.Combobox(self.master, values=self.get_model_presets())
        self.model_selection.bind('<<ComboboxSelected>>', self.on_model_selected)
        self.model_selection.pack()

    def get_model_presets(self):
        return [
            'CLIP',
            'DINOv2',
            'timm',
            'CLIP+DINOv2',
            'CLIP+timm',
            'DINOv2+timm',
            'CLIP+DINOv2+timm'
        ]

    def on_model_selected(self, event):
        selected_model = event.widget.get()
        if selected_model in ['CLIP+DINOv2', 'CLIP+timm', 'DINOv2+timm', 'CLIP+DINOv2+timm']:
            self.show_performance_warning(selected_model)
        self.handle_selected_model(selected_model)

    def show_performance_warning(self, model):
        warning_message = f'Warning: {model} may perform slower due to combined presets.'
        print(warning_message)

    def handle_selected_model(self, model):
        # Backend logic for handling combined models without TorchScript compilation of timm
        print(f'Handling model: {model}')  

# Assuming this code is placed within the appropriate Tkinter application context
