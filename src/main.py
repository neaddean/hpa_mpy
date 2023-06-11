from app import App
from util import gc_collect

app = App()

app.start()

gc_collect()
