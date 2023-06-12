from app import App
from util import gc_collect

app = App()

app.go()

gc_collect()
