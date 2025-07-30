import kivy
from kivy.app import App
from kivy.uix.webview import WebView
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.utils import platform

class VGKApp(App):
    def build(self):
        # Set window size for desktop testing
        if platform == 'desktop':
            Window.size = (400, 700)
        
        layout = BoxLayout(orientation='vertical')
        
        # Create WebView to load the PWA
        webview = WebView(url='http://localhost:8000')
        layout.add_widget(webview)
        
        return layout

if __name__ == '__main__':
    VGKApp().run()
